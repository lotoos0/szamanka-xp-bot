"""Voice role management based on total_voice_sec."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml
import discord

logger = logging.getLogger("xpbot.roles")


@dataclass
class RoleTier:
    """Single role tier configuration."""

    name: str
    role_id: int
    min_minutes: int

    @property
    def min_seconds(self) -> int:
        """Minimum seconds required for this tier."""
        return self.min_minutes * 60


@dataclass
class GuildRolesConfig:
    """Guild-specific roles configuration."""

    guild_id: int
    tiers: list[RoleTier]

    def get_eligible_tier(self, total_voice_sec: int) -> Optional[RoleTier]:
        """
        Get the highest tier the user qualifies for.

        Args:
            total_voice_sec: Total voice seconds for the user

        Returns:
            The highest RoleTier the user qualifies for, or None
        """
        eligible_tiers = [
            tier for tier in self.tiers
            if total_voice_sec >= tier.min_seconds
        ]

        if not eligible_tiers:
            return None

        # Return the tier with highest min_minutes requirement
        return max(eligible_tiers, key=lambda t: t.min_minutes)

    def get_all_role_ids(self) -> set[int]:
        """Get all role IDs configured for this guild."""
        return {tier.role_id for tier in self.tiers}


def load_roles_config(config_path: str | Path = "config/roles_config.yaml") -> dict[int, GuildRolesConfig]:
    """
    Load roles configuration from YAML file.

    Args:
        config_path: Path to roles_config.yaml file

    Returns:
        Dictionary mapping guild_id -> GuildRolesConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is malformed
    """
    # Convert to Path and resolve relative to project root
    if not isinstance(config_path, Path):
        config_path = Path(config_path)

    if not config_path.is_absolute():
        # Assuming we're in src/bot/, go up to project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / config_path

    if not config_path.exists():
        raise FileNotFoundError(f"Roles config not found: {config_path}")

    logger.info(f"Loading roles config from {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    if not data or "guilds" not in data:
        raise ValueError("Invalid roles config: missing 'guilds' key")

    roles_config = {}

    for guild_id_str, guild_data in data["guilds"].items():
        guild_id = int(guild_id_str)

        if "tiers" not in guild_data:
            logger.warning(f"Guild {guild_id} has no tiers configured, skipping")
            continue

        tiers = []
        for tier_data in guild_data["tiers"]:
            try:
                tier = RoleTier(
                    name=tier_data["name"],
                    role_id=int(tier_data["role_id"]),
                    min_minutes=int(tier_data["min_minutes"]),
                )
                tiers.append(tier)
            except (KeyError, ValueError) as e:
                logger.error(f"Invalid tier config in guild {guild_id}: {e}")
                continue

        if tiers:
            # Sort tiers by min_minutes ascending
            tiers.sort(key=lambda t: t.min_minutes)
            roles_config[guild_id] = GuildRolesConfig(guild_id=guild_id, tiers=tiers)
            logger.info(f"Loaded {len(tiers)} role tiers for guild {guild_id}")
        else:
            logger.warning(f"Guild {guild_id} has no valid tiers, skipping")

    logger.info(f"Roles config loaded for {len(roles_config)} guild(s)")
    return roles_config


async def update_user_voice_role(
    member: discord.Member,
    guild_roles: GuildRolesConfig,
    total_voice_sec: int,
) -> None:
    """
    Update user's voice tier role based on total_voice_sec.

    Assigns the highest tier role the user qualifies for and removes
    lower tier roles. Only one voice tier role is assigned at a time.

    Args:
        member: Discord member to update
        guild_roles: Guild's role configuration
        total_voice_sec: Total voice seconds for the member

    Note:
        Requires bot to have MANAGE_ROLES permission and bot's highest
        role must be above all configured tier roles in the hierarchy.
    """
    # Check if bot has permission to manage roles
    if not member.guild.me.guild_permissions.manage_roles:
        logger.error(f"Bot missing MANAGE_ROLES permission in guild {member.guild.id} ({member.guild.name})")
        return

    # Find which tier the user should have (if any)
    eligible_tier = guild_roles.get_eligible_tier(total_voice_sec)

    # Get all voice-tier role IDs from config
    voice_role_ids = guild_roles.get_all_role_ids()

    # Get bot's top role for hierarchy checking
    bot_top_role = member.guild.me.top_role

    # Find which voice-tier roles the member currently has
    current_voice_roles = [role for role in member.roles if role.id in voice_role_ids]

    # Determine what changes need to be made
    if eligible_tier is None:
        # User doesn't qualify for any tier - remove all voice roles
        if current_voice_roles:
            logger.info(
                f"User {member.display_name} ({member.id}) doesn't qualify for any tier "
                f"({total_voice_sec}s = {total_voice_sec // 60}min). Removing {len(current_voice_roles)} role(s)."
            )
            roles_to_remove = current_voice_roles
            roles_to_add = []
        else:
            # User has no voice roles and shouldn't have any - nothing to do
            logger.debug(
                f"User {member.display_name} ({member.id}) has no voice roles and doesn't qualify for any "
                f"({total_voice_sec}s = {total_voice_sec // 60}min)"
            )
            return
    else:
        # User qualifies for a tier
        target_role = member.guild.get_role(eligible_tier.role_id)

        if target_role is None:
            logger.error(
                f"Role {eligible_tier.role_id} ({eligible_tier.name}) not found in guild {member.guild.id}. "
                f"Check roles_config.yaml"
            )
            return

        # Check role hierarchy - bot must be able to assign this role
        if target_role >= bot_top_role:
            logger.error(
                f"Cannot assign role {target_role.name} to {member.display_name}: "
                f"role is at or above bot's highest role ({bot_top_role.name}). "
                f"Move bot's role higher in server settings."
            )
            return

        # Check if user already has the correct role
        if target_role in current_voice_roles and len(current_voice_roles) == 1:
            # User already has exactly this role - nothing to do
            logger.debug(
                f"User {member.display_name} ({member.id}) already has correct role: "
                f"{target_role.name} ({total_voice_sec}s = {total_voice_sec // 60}min)"
            )
            return

        # User needs role change
        roles_to_remove = [role for role in current_voice_roles if role.id != eligible_tier.role_id]
        roles_to_add = [target_role] if target_role not in current_voice_roles else []

        logger.info(
            f"User {member.display_name} ({member.id}) qualifies for tier '{eligible_tier.name}' "
            f"({total_voice_sec}s = {total_voice_sec // 60}min). "
            f"Adding: {[r.name for r in roles_to_add]}, "
            f"Removing: {[r.name for r in roles_to_remove]}"
        )

    # Apply role changes with error handling
    try:
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Voice tier role update")
            logger.info(f"Removed roles from {member.display_name}: {[r.name for r in roles_to_remove]}")

        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Voice tier role update")
            logger.info(f"Added roles to {member.display_name}: {[r.name for r in roles_to_add]}")

    except discord.Forbidden:
        logger.error(
            f"Missing permissions to manage roles for {member.display_name} ({member.id}) "
            f"in guild {member.guild.name}. Check bot permissions and role hierarchy."
        )
    except discord.HTTPException as e:
        logger.error(
            f"Failed to update roles for {member.display_name} ({member.id}): {e}",
            exc_info=True
        )

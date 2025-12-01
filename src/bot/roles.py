"""Voice role management based on total_voice_sec."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

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


# TODO: DAY06.5 - implement update_user_voice_role

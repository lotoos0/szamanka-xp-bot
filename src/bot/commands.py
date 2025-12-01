"""Slash commands implementation."""

import logging
import discord
from discord.ext import commands

from .db import get_leaderboard, get_user_stats, get_user_rank
from .models import xp_needed_for_level

logger = logging.getLogger("xpbot.commands")

# Medal emojis for top 3
MEDALS = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
}


async def leaderboard(ctx: discord.ApplicationContext):
    """
    Show top 10 users by XP on this server.

    Args:
        ctx: Discord application context
    """
    await ctx.defer()  # This can take a moment, so defer the response

    guild_id = ctx.guild.id

    try:
        # Get top 10 users from database
        top_users = await get_leaderboard(guild_id, limit=10)

        if not top_users:
            await ctx.respond(
                "📊 **Leaderboard**\n\n"
                "No users found yet. Start spending time in voice channels to earn XP!",
                ephemeral=True
            )
            return

        # Build the message as plain text
        lines = [
            "🏆 **XP Leaderboard**",
            f"*Top {len(top_users)} users on {ctx.guild.name}*",
            ""  # Empty line for spacing
        ]

        # Add users
        for rank, user_stats in enumerate(top_users, 1):
            # Try to get the Discord user object
            user = ctx.guild.get_member(user_stats.user_id)

            # Get medal for top 3, otherwise just number
            medal = MEDALS.get(rank, f"#{rank}")

            # Build line
            if user:
                line = f"{medal} {user.mention} - **LVL: {user_stats.level}**"
            else:
                line = f"{medal} Unknown User - **LVL: {user_stats.level}**"

            lines.append(line)

        # Add footer
        lines.append("")  # Empty line
        lines.append(f"*Earn {6} XP per minute in voice channels*")

        # Join all lines and send
        message = "\n".join(lines)
        await ctx.respond(message)
        logger.info(f"/leaderboard used in {ctx.guild.name} by {ctx.author}")

    except Exception as e:
        logger.error(f"Error in /leaderboard: {e}", exc_info=True)
        await ctx.respond(
            "❌ An error occurred while fetching the leaderboard. Please try again later.",
            ephemeral=True
        )


async def rank(ctx: discord.ApplicationContext, user: discord.Member = None):
    """
    Show XP rank and stats for a user.

    Args:
        ctx: Discord application context
        user: Optional user to check (defaults to command author)
    """
    await ctx.defer()

    # Default to command author if no user specified
    target_user = user or ctx.author
    guild_id = ctx.guild.id

    try:
        # Get user stats from database
        stats = await get_user_stats(guild_id, target_user.id)

        if not stats:
            if target_user == ctx.author:
                await ctx.respond(
                    "You don't have any XP yet! Join a voice channel to start earning XP.",
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    f"{target_user.mention} doesn't have any XP yet!",
                    ephemeral=True
                )
            return

        # Get user's rank
        user_rank = await get_user_rank(guild_id, target_user.id)

        # Calculate XP needed for next level
        xp_needed = xp_needed_for_level(stats.level)
        xp_progress = f"{stats.xp_into_level:,} / {xp_needed:,}"
        xp_percentage = int((stats.xp_into_level / xp_needed) * 100) if xp_needed > 0 else 0

        # Format voice time
        hours = int(stats.total_voice_hours)
        minutes = int((stats.total_voice_hours - hours) * 60)
        voice_time = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # Build the message
        lines = [
            f"📊 **Rank Stats for {target_user.display_name}**",
            ""
        ]

        # Add rank position
        if user_rank:
            lines.append(f"🏆 **Rank:** #{user_rank}")

        # Add level and XP
        lines.append(f"⭐ **Level:** {stats.level}")
        lines.append(f"💎 **XP:** {xp_progress} ({xp_percentage}%)")
        lines.append(f"📈 **Total XP:** {stats.total_xp:,}")

        # Add voice time
        lines.append(f"🎤 **Voice Time:** {voice_time}")

        # Join and send
        message = "\n".join(lines)
        await ctx.respond(message)

        logger.info(f"/rank used for {target_user} in {ctx.guild.name} by {ctx.author}")

    except Exception as e:
        logger.error(f"Error in /rank: {e}", exc_info=True)
        await ctx.respond(
            "❌ An error occurred while fetching rank data. Please try again later.",
            ephemeral=True
        )

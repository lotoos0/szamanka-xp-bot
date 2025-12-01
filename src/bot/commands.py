"""Slash commands implementation."""

import logging
import discord
from discord.ext import commands

from .db import get_leaderboard

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

        # Build the embed
        embed = discord.Embed(
            title="🏆 XP Leaderboard",
            description=f"Top {len(top_users)} users on {ctx.guild.name}",
            color=discord.Color.gold()
        )

        # Add users to embed
        leaderboard_text = []
        for rank, user_stats in enumerate(top_users, 1):
            # Try to get the Discord user object
            user = ctx.guild.get_member(user_stats.user_id)
            username = user.display_name if user else f"User {user_stats.user_id}"

            # Get medal for top 3
            medal = MEDALS.get(rank, f"`#{rank}`")

            # Format voice time
            hours = user_stats.total_voice_hours
            if hours >= 1:
                time_str = f"{hours:.1f}h"
            else:
                time_str = f"{user_stats.total_voice_minutes}m"

            # Build line
            line = (
                f"{medal} **{username}** - "
                f"Level {user_stats.level} ({user_stats.total_xp:,} XP) • "
                f"{time_str} voice"
            )
            leaderboard_text.append(line)

        embed.description = "\n".join(leaderboard_text)

        # Add footer
        embed.set_footer(text=f"Earn {6} XP per minute in voice channels")

        await ctx.respond(embed=embed)
        logger.info(f"/leaderboard used in {ctx.guild.name} by {ctx.author}")

    except Exception as e:
        logger.error(f"Error in /leaderboard: {e}", exc_info=True)
        await ctx.respond(
            "❌ An error occurred while fetching the leaderboard. Please try again later.",
            ephemeral=True
        )


# TODO: DAY06 - implement /rank

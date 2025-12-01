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


# TODO: DAY06 - implement /rank

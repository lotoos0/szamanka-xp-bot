"""Main bot entry point."""

import discord
from discord.ext import commands
import logging

from .config import Config
from . import db
from .commands import leaderboard, rank

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("xpbot")


# Bot setup with intents
intents = discord.Intents.default()
intents.voice_states = True  # Required for voice tracking (DAY07+)
intents.guilds = True
intents.members = True  # Required for member info

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    """Called when bot is ready and connected."""
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    # Initialize database connection pool
    try:
        await db.init_db_pool()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        logger.warning("Bot will continue without database functionality")

    # Sync slash commands (force update)
    logger.info("Syncing slash commands with Discord...")
    await bot.sync_commands()
    logger.info(f"Synced {len(bot.pending_application_commands)} slash commands")

    logger.info("XPBot is ready!")


@bot.event
async def on_close():
    """Called when bot is shutting down."""
    logger.info("Bot shutting down...")
    await db.close_db_pool()
    logger.info("Database connection closed")


@bot.slash_command(name="ping", description="Check if bot is online")
async def ping(ctx: discord.ApplicationContext):
    """Simple ping command to verify bot is responding."""
    latency_ms = round(bot.latency * 1000)
    await ctx.respond(
        f"🤖 **XPBot online!**\n"
        f"Latency: `{latency_ms}ms`\n"
        f"Ready to track voice XP!"
    )
    logger.info(f"/ping used by {ctx.author} in {ctx.guild.name}")


@bot.slash_command(name="leaderboard", description="Show top 10 users by XP")
async def leaderboard_command(ctx: discord.ApplicationContext):
    """Show the XP leaderboard."""
    await leaderboard(ctx)


@bot.slash_command(name="rank", description="Show your XP rank and stats")
async def rank_command(
    ctx: discord.ApplicationContext,
    user: discord.Option(discord.Member, description="User to check (optional)", required=False, default=None)
):
    """Show rank stats for a user."""
    await rank(ctx, user)


def main():
    """Start the bot."""
    logger.info("Starting Discord XP Bot...")
    logger.info(f"XP Rate: {Config.XP_PER_MINUTE} XP/min")

    try:
        bot.run(Config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Failed to login - check your DISCORD_TOKEN in .env")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)


if __name__ == "__main__":
    main()

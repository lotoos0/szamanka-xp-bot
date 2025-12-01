"""Database connection and query helpers."""

import logging
from typing import Optional
import asyncpg

from .config import Config
from .models import UserStats

logger = logging.getLogger("xpbot.db")

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> asyncpg.Pool:
    """Initialize database connection pool."""
    global _pool

    if _pool is not None:
        return _pool

    logger.info("Connecting to PostgreSQL...")
    _pool = await asyncpg.create_pool(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        database=Config.POSTGRES_DB,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )
    logger.info("Database connection pool created")
    return _pool


async def close_db_pool() -> None:
    """Close database connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


def get_pool() -> asyncpg.Pool:
    """Get the database connection pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _pool


async def get_user_stats(guild_id: int, user_id: int) -> Optional[UserStats]:
    """
    Get user statistics from database.

    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID

    Returns:
        UserStats object if found, None otherwise
    """
    pool = get_pool()

    query = """
        SELECT guild_id, user_id, total_xp, level, xp_into_level,
               total_voice_sec, last_voice_join, updated_at
        FROM user_stats
        WHERE guild_id = $1 AND user_id = $2
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, guild_id, user_id)

    if row is None:
        return None

    return UserStats(
        guild_id=row["guild_id"],
        user_id=row["user_id"],
        total_xp=row["total_xp"],
        level=row["level"],
        xp_into_level=row["xp_into_level"],
        total_voice_sec=row["total_voice_sec"],
        last_voice_join=row["last_voice_join"],
        updated_at=row["updated_at"],
    )


async def upsert_user_stats(stats: UserStats) -> None:
    """
    Insert or update user statistics in database.

    Args:
        stats: UserStats object to save
    """
    pool = get_pool()

    query = """
        INSERT INTO user_stats
            (guild_id, user_id, total_xp, level, xp_into_level,
             total_voice_sec, last_voice_join, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        ON CONFLICT (guild_id, user_id)
        DO UPDATE SET
            total_xp = EXCLUDED.total_xp,
            level = EXCLUDED.level,
            xp_into_level = EXCLUDED.xp_into_level,
            total_voice_sec = EXCLUDED.total_voice_sec,
            last_voice_join = EXCLUDED.last_voice_join,
            updated_at = NOW()
    """

    async with pool.acquire() as conn:
        await conn.execute(
            query,
            stats.guild_id,
            stats.user_id,
            stats.total_xp,
            stats.level,
            stats.xp_into_level,
            stats.total_voice_sec,
            stats.last_voice_join,
        )


async def get_leaderboard(guild_id: int, limit: int = 10) -> list[UserStats]:
    """
    Get top users by XP for a guild.

    Args:
        guild_id: Discord guild ID
        limit: Maximum number of users to return

    Returns:
        List of UserStats objects sorted by total_xp descending
    """
    pool = get_pool()

    query = """
        SELECT guild_id, user_id, total_xp, level, xp_into_level,
               total_voice_sec, last_voice_join, updated_at
        FROM user_stats
        WHERE guild_id = $1
        ORDER BY total_xp DESC, total_voice_sec DESC, user_id ASC
        LIMIT $2
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, guild_id, limit)

    return [
        UserStats(
            guild_id=row["guild_id"],
            user_id=row["user_id"],
            total_xp=row["total_xp"],
            level=row["level"],
            xp_into_level=row["xp_into_level"],
            total_voice_sec=row["total_voice_sec"],
            last_voice_join=row["last_voice_join"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


async def get_user_rank(guild_id: int, user_id: int) -> Optional[int]:
    """
    Get user's position in the leaderboard (1-indexed).

    Args:
        guild_id: Discord guild ID
        user_id: Discord user ID

    Returns:
        User's rank (1 = top), or None if user not found
    """
    pool = get_pool()

    query = """
        WITH ranked_users AS (
            SELECT user_id,
                   ROW_NUMBER() OVER (
                       ORDER BY total_xp DESC, total_voice_sec DESC, user_id ASC
                   ) as rank
            FROM user_stats
            WHERE guild_id = $1
        )
        SELECT rank FROM ranked_users WHERE user_id = $2
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, guild_id, user_id)

    return row["rank"] if row else None

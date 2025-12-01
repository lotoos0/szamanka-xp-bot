#!/usr/bin/env python3
"""Seed database with test user data."""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import bot modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from bot.db import init_db_pool, close_db_pool, upsert_user_stats, get_user_stats
from bot.models import UserStats


async def seed_test_data():
    """Insert test users with various XP levels."""

    # Initialize database pool
    await init_db_pool()
    print("Connected to database")

    # Test guild ID (replace with your actual server ID for real testing)
    guild_id = 123456789012345678

    # Test users with different levels
    test_users = [
        # High level users
        UserStats(
            guild_id=guild_id,
            user_id=111111111111111111,
            total_xp=15000,
            level=25,
            xp_into_level=450,
            total_voice_sec=150000,  # ~41.7 hours
        ),
        UserStats(
            guild_id=guild_id,
            user_id=222222222222222222,
            total_xp=12000,
            level=22,
            xp_into_level=320,
            total_voice_sec=120000,  # ~33.3 hours
        ),
        UserStats(
            guild_id=guild_id,
            user_id=333333333333333333,
            total_xp=8500,
            level=18,
            xp_into_level=150,
            total_voice_sec=85000,  # ~23.6 hours
        ),
        # Mid level users
        UserStats(
            guild_id=guild_id,
            user_id=444444444444444444,
            total_xp=5000,
            level=14,
            xp_into_level=80,
            total_voice_sec=50000,  # ~13.9 hours
        ),
        UserStats(
            guild_id=guild_id,
            user_id=555555555555555555,
            total_xp=3000,
            level=10,
            xp_into_level=200,
            total_voice_sec=30000,  # ~8.3 hours
        ),
        # Low level users
        UserStats(
            guild_id=guild_id,
            user_id=666666666666666666,
            total_xp=1500,
            level=7,
            xp_into_level=50,
            total_voice_sec=15000,  # ~4.2 hours
        ),
        UserStats(
            guild_id=guild_id,
            user_id=777777777777777777,
            total_xp=500,
            level=3,
            xp_into_level=20,
            total_voice_sec=5000,  # ~1.4 hours
        ),
        UserStats(
            guild_id=guild_id,
            user_id=888888888888888888,
            total_xp=150,
            level=1,
            xp_into_level=0,
            total_voice_sec=1500,  # ~25 minutes
        ),
    ]

    # Insert all test users
    for user in test_users:
        await upsert_user_stats(user)
        print(f"✓ Inserted user {user.user_id}: Level {user.level}, {user.total_xp} XP, "
              f"{user.total_voice_hours:.1f}h voice")

    print(f"\n{len(test_users)} test users inserted successfully!")

    # Verify by reading one back
    print("\nVerifying data...")
    first_user = await get_user_stats(guild_id, test_users[0].user_id)
    if first_user:
        print(f"✓ Successfully read back user {first_user.user_id}")
        print(f"  Level: {first_user.level}, XP: {first_user.total_xp}, "
              f"Voice: {first_user.total_voice_hours:.1f}h")
    else:
        print("✗ Failed to read back user data")

    # Close pool
    await close_db_pool()
    print("\nDatabase connection closed")


if __name__ == "__main__":
    asyncio.run(seed_test_data())

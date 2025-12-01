#!/usr/bin/env python3
"""Test database functions."""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from bot.db import init_db_pool, close_db_pool, get_leaderboard, get_user_rank


async def test_leaderboard():
    """Test leaderboard and rank functions."""

    await init_db_pool()
    print("Connected to database\n")

    guild_id = 123456789012345678

    # Test leaderboard
    print("=== TOP 5 LEADERBOARD ===")
    top_users = await get_leaderboard(guild_id, limit=5)
    for i, user in enumerate(top_users, 1):
        print(f"{i}. User {user.user_id}: Level {user.level}, {user.total_xp} XP, "
              f"{user.total_voice_hours:.1f}h voice")

    # Test user rank
    print("\n=== USER RANKS ===")
    test_user_ids = [111111111111111111, 555555555555555555, 888888888888888888]
    for user_id in test_user_ids:
        rank = await get_user_rank(guild_id, user_id)
        if rank:
            print(f"User {user_id} is rank #{rank}")
        else:
            print(f"User {user_id} not found")

    await close_db_pool()
    print("\nDatabase connection closed")


if __name__ == "__main__":
    asyncio.run(test_leaderboard())

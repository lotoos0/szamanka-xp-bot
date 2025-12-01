#!/usr/bin/env python3
"""Test roles configuration loader."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from bot.roles import load_roles_config


def test_roles_config():
    """Test loading and using roles configuration."""

    print("Loading roles configuration...")
    roles_config = load_roles_config()

    print(f"\n✓ Loaded config for {len(roles_config)} guild(s)\n")

    for guild_id, config in roles_config.items():
        print(f"Guild {guild_id}:")
        print(f"  Total tiers: {len(config.tiers)}")
        for tier in config.tiers:
            hours = tier.min_minutes / 60
            print(f"    - {tier.name}: {tier.min_minutes} min ({hours:.1f}h) -> Role ID {tier.role_id}")

        # Test tier selection logic
        print(f"\n  Testing tier selection:")
        test_cases = [
            (0, "0 minutes"),
            (60 * 60, "1 hour"),
            (5 * 60 * 60, "5 hours"),
            (20 * 60 * 60, "20 hours"),
            (60 * 60 * 60, "60 hours"),
            (150 * 60 * 60, "150 hours"),
        ]

        for seconds, desc in test_cases:
            tier = config.get_eligible_tier(seconds)
            if tier:
                print(f"    {desc:15s} -> {tier.name}")
            else:
                print(f"    {desc:15s} -> No tier")

        print(f"\n  All role IDs: {config.get_all_role_ids()}\n")


if __name__ == "__main__":
    test_roles_config()

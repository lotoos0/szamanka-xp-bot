"""Data models and dataclasses."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserStats:
    """User XP and voice statistics."""

    guild_id: int
    user_id: int
    total_xp: int = 0
    level: int = 0
    xp_into_level: int = 0
    total_voice_sec: int = 0
    last_voice_join: datetime | None = None
    updated_at: datetime | None = None

    @property
    def total_voice_hours(self) -> float:
        """Total voice time in hours."""
        return self.total_voice_sec / 3600

    @property
    def total_voice_minutes(self) -> int:
        """Total voice time in minutes."""
        return self.total_voice_sec // 60

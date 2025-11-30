"""Configuration management - loads from .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path)


class Config:
    """Bot configuration loaded from environment variables."""

    # Discord
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

    # PostgreSQL
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "discord_xp_bot")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "xpbot")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # Bot Settings
    XP_PER_MINUTE: int = int(os.getenv("XP_PER_MINUTE", "6"))
    LEVELUP_ANNOUNCE_ENABLED: bool = os.getenv("LEVELUP_ANNOUNCE_ENABLED", "false").lower() == "true"
    LEVELUP_CHANNEL_ID: int | None = int(os.getenv("LEVELUP_CHANNEL_ID")) if os.getenv("LEVELUP_CHANNEL_ID") else None

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required in .env file")
        if not cls.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD is required in .env file")

    @classmethod
    def get_postgres_dsn(cls) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )


# Validate on import
Config.validate()

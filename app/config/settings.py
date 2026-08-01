"""Application settings loaded from environment variables.

Uses Pydantic Settings for type-safe configuration management.
Supports .env file and environment variables.
"""

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str
    admin_telegram_id: int = 0

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    # Paths
    download_dir: Path = Path("./data/downloads")
    cache_dir: Path = Path("./data/cache")
    log_dir: Path = Path("./logs")

    # Limits
    max_file_size_mb: int = 2000
    rate_limit_per_user: int = 5
    rate_limit_window_seconds: int = 60

    # FFmpeg
    ffmpeg_path: str = "ffmpeg"

    # Logging
    log_level: str = "INFO"

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        Path(self.database_url.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()

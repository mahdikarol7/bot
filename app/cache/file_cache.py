"""File-based cache for downloaded files.

Avoids re-downloading files that already exist in cache.
Cache key is based on video ID + download type + quality.
"""

import hashlib
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings


class FileCache:
    """Simple file cache keyed by content hash."""

    def __init__(self) -> None:
        settings = get_settings()
        self.cache_dir = settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _make_key(video_id: str, download_type: str, quality: str) -> str:
        """Generate a unique cache key."""
        raw = f"{video_id}:{download_type}:{quality}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get_cached_file(
        self, video_id: str, download_type: str, quality: str
    ) -> Path | None:
        """Return the cached file path if it exists, else None."""
        key = self._make_key(video_id, download_type, quality)
        ext = ".mp3" if download_type == "audio" else ".mp4"
        cached = self.cache_dir / f"{key}{ext}"
        if cached.exists() and cached.stat().st_size > 0:
            logger.debug("Cache hit for {}", key)
            return cached
        logger.debug("Cache miss for {}", key)
        return None

    def get_cache_path(
        self, video_id: str, download_type: str, quality: str
    ) -> Path:
        """Return the expected cache path (creates parent dirs)."""
        key = self._make_key(video_id, download_type, quality)
        ext = ".mp3" if download_type == "audio" else ".mp4"
        return self.cache_dir / f"{key}{ext}"

    def get_cache_size(self) -> int:
        """Return total cache size in bytes."""
        total = 0
        for f in self.cache_dir.iterdir():
            if f.is_file():
                total += f.stat().st_size
        return total

    def clear_cache(self) -> int:
        """Remove all cached files. Returns number of files removed."""
        count = 0
        for f in self.cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        logger.info("Cache cleared: {} files removed", count)
        return count

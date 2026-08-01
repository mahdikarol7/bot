"""Tests for file cache."""

import tempfile
from pathlib import Path

from app.cache.file_cache import FileCache


class TestFileCache:
    """Tests for file-based caching."""

    def test_cache_miss(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.cache.file_cache.get_settings", lambda: type(
            "Settings", (), {"cache_dir": tmp_path}
        )())
        cache = FileCache()
        result = cache.get_cached_file("test123", "video", "720p")
        assert result is None

    def test_cache_hit(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.cache.file_cache.get_settings", lambda: type(
            "Settings", (), {"cache_dir": tmp_path}
        )())
        cache = FileCache()

        # Create a cached file
        cache_path = cache.get_cache_path("test123", "video", "720p")
        cache_path.write_bytes(b"fake video data")

        result = cache.get_cached_file("test123", "video", "720p")
        assert result is not None
        assert result.exists()

    def test_cache_key_deterministic(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.cache.file_cache.get_settings", lambda: type(
            "Settings", (), {"cache_dir": tmp_path}
        )())
        cache = FileCache()

        path1 = cache.get_cache_path("test123", "video", "720p")
        path2 = cache.get_cache_path("test123", "video", "720p")
        assert path1 == path2

    def test_different_keys_different_paths(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.cache.file_cache.get_settings", lambda: type(
            "Settings", (), {"cache_dir": tmp_path}
        )())
        cache = FileCache()

        path1 = cache.get_cache_path("test123", "video", "720p")
        path2 = cache.get_cache_path("test123", "audio", "128 kbps")
        assert path1 != path2

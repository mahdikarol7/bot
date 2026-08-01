"""Tests for file utility functions."""

from app.utils.file_utils import (
    sanitize_filename,
    format_duration,
    format_views,
    format_file_size,
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_normal_filename(self):
        assert sanitize_filename("My Video Title") == "My Video Title"

    def test_removes_illegal_chars(self):
        result = sanitize_filename('Video: "Best" <2024>')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result

    def test_empty_string(self):
        assert sanitize_filename("") == "download"

    def test_dots_only(self):
        assert sanitize_filename("...") == "download"

    def test_truncates_long_name(self):
        long_name = "A" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200


class TestFormatDuration:
    """Tests for duration formatting."""

    def test_zero_seconds(self):
        assert format_duration(0) == "00:00"

    def test_minutes_only(self):
        assert format_duration(125) == "02:05"

    def test_hours_minutes_seconds(self):
        assert format_duration(3661) == "01:01:01"

    def test_negative(self):
        assert format_duration(-10) == "00:00"


class TestFormatViews:
    """Tests for view count formatting."""

    def test_small_number(self):
        assert format_views(500) == "500"

    def test_thousands(self):
        assert format_views(1500) == "1.5K"

    def test_millions(self):
        assert format_views(2500000) == "2.5M"

    def test_billions(self):
        assert format_views(1500000000) == "1.5B"


class TestFormatFileSize:
    """Tests for file size formatting."""

    def test_bytes(self):
        assert format_file_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_file_size(1048576) == "1.0 MB"

    def test_gigabytes(self):
        assert format_file_size(1073741824) == "1.0 GB"

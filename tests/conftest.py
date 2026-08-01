"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_youtube_urls() -> list[str]:
    """Sample valid YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]


@pytest.fixture
def sample_invalid_urls() -> list[str]:
    """Sample invalid URLs for testing."""
    return [
        "https://www.google.com",
        "not a url",
        "https://youtube.com/watch?v=short",
        "",
        "ftp://youtube.com/video.mp4",
        "https://vimeo.com/123456",
    ]

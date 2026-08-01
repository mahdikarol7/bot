"""Tests for URL validation utilities."""

from app.utils.url_validator import is_valid_youtube_url, extract_video_id


class TestURLValidation:
    """Tests for YouTube URL validation."""

    def test_valid_standard_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_short_url(self):
        assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_valid_shorts_url(self):
        assert is_valid_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")

    def test_valid_http_url(self):
        assert is_valid_youtube_url("http://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_with_extra_params(self):
        assert is_valid_youtube_url(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        )

    def test_invalid_url(self):
        assert not is_valid_youtube_url("https://www.google.com")

    def test_invalid_text(self):
        assert not is_valid_youtube_url("not a url")

    def test_empty_string(self):
        assert not is_valid_youtube_url("")

    def test_invalid_short_id(self):
        assert not is_valid_youtube_url("https://youtube.com/watch?v=short")


class TestVideoIDExtraction:
    """Tests for video ID extraction."""

    def test_standard_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_with_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        assert extract_video_id("https://www.google.com") is None

    def test_invalid_id_length(self):
        assert extract_video_id("https://youtube.com/watch?v=short") is None

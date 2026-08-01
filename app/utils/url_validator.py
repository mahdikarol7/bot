"""YouTube URL validation utilities."""

import re
from urllib.parse import urlparse, parse_qs

# YouTube URL patterns
_YT_VIDEO_PATTERN = re.compile(
    r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}(&[\w=&-]*)?$"
)
_YT_SHORT_PATTERN = re.compile(
    r"^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}(\?[\w=&-]*)?$"
)
_YT_SHORT_LINK = re.compile(
    r"^(https?://)?youtu\.be/[\w-]{11}(\?[\w=&-]*)?$"
)

SUPPORTED_PATTERNS = [_YT_VIDEO_PATTERN, _YT_SHORT_PATTERN, _YT_SHORT_LINK]


def is_valid_youtube_url(url: str) -> bool:
    """Check if a URL is a valid YouTube video or shorts URL."""
    url = url.strip()
    return any(pattern.match(url) for pattern in SUPPORTED_PATTERNS)


def extract_video_id(url: str) -> str | None:
    """Extract the 11-character video ID from a YouTube URL."""
    url = url.strip()

    # Handle youtu.be short links
    short_match = re.match(r"^(https?://)?youtu\.be/([\w-]{11})", url)
    if short_match:
        return short_match.group(2)

    # Handle /shorts/ links
    shorts_match = re.match(
        r"^(https?://)?(www\.)?youtube\.com/shorts/([\w-]{11})", url
    )
    if shorts_match:
        return shorts_match.group(3)

    # Handle standard /watch?v= links
    parsed = urlparse(url)
    if parsed.hostname in ("youtube.com", "www.youtube.com"):
        query = parse_qs(parsed.query)
        video_ids = query.get("v")
        if video_ids and len(video_ids[0]) == 11:
            return video_ids[0]

    return None

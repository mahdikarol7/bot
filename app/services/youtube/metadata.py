"""YouTube metadata extraction service.

Extracts video information using yt-dlp without downloading.
"""

from dataclasses import dataclass

import yt_dlp
from loguru import logger

from app.utils.file_utils import format_duration


@dataclass
class VideoMetadata:
    """Structured video metadata."""
    video_id: str
    title: str
    channel: str
    thumbnail: str
    duration: int  # seconds
    duration_formatted: str
    view_count: int
    available_formats: list[dict]


async def extract_metadata(url: str) -> VideoMetadata:
    """Extract video metadata from a YouTube URL.

    Args:
        url: YouTube video or shorts URL.

    Returns:
        VideoMetadata with all extracted info.

    Raises:
        yt_dlp.utils.DownloadError: If video cannot be accessed.
    """
    logger.info("Extracting metadata for: {}", url)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await _extract_info(ydl, url)

    formats = info.get("formats", [])

    return VideoMetadata(
        video_id=info.get("id", ""),
        title=info.get("title", "Unknown"),
        channel=info.get("channel", info.get("uploader", "Unknown")),
        thumbnail=info.get("thumbnail", ""),
        duration=info.get("duration", 0),
        duration_formatted=format_duration(info.get("duration", 0)),
        view_count=info.get("view_count", 0),
        available_formats=formats,
    )


async def _extract_info(ydl: yt_dlp.YoutubeDL, url: str) -> dict:
    """Run yt-dlp extraction in a thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))


def get_available_video_qualities(metadata: VideoMetadata) -> list[dict]:
    """Filter and return available video qualities.

    Returns list of dicts with 'format_id', 'resolution', 'ext'.
    Only includes formats that have both video and audio, or video-only
    (we'll merge audio separately with FFmpeg).
    """
    seen_resolutions: dict[str, dict] = {}

    for fmt in metadata.available_formats:
        if fmt.get("vcodec") == "none":
            continue  # Skip audio-only formats

        height = fmt.get("height")
        if not height:
            continue

        resolution = f"{height}p"

        # Map to our supported qualities
        supported = {"360": "360p", "480": "480p", "720": "720p", "1080": "1080p"}
        str_height = str(height)
        if str_height not in supported:
            continue

        label = supported[str_height]
        if label not in seen_resolutions:
            seen_resolutions[label] = {
                "format_id": fmt.get("format_id", ""),
                "resolution": label,
                "height": height,
                "ext": fmt.get("ext", "mp4"),
                "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
            }

    # Sort by height
    qualities = sorted(seen_resolutions.values(), key=lambda x: x["height"])
    return qualities


def get_available_audio_qualities(metadata: VideoMetadata) -> list[dict]:
    """Return available audio-only qualities."""
    seen: dict[str, dict] = {}

    for fmt in metadata.available_formats:
        if fmt.get("acodec") == "none":
            continue
        if fmt.get("vcodec") != "none":
            continue  # Skip video formats

        abr = fmt.get("abr", 0)
        if abr <= 0:
            continue

        # Map to our supported qualities
        if abr <= 128:
            label = "128 kbps"
        elif abr <= 192:
            label = "192 kbps"
        elif abr <= 320:
            label = "320 kbps"
        else:
            label = "Best Audio"

        if label not in seen:
            seen[label] = {
                "format_id": fmt.get("format_id", ""),
                "quality": label,
                "abr": abr,
            }

    return list(seen.values())

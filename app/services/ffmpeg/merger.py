"""FFmpeg video/audio merger.

Merges separate video and audio streams into a single MP4 file.
"""

import asyncio
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings


async def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
) -> str:
    """Merge separate video and audio files into one MP4.

    Uses FFmpeg to combine streams without re-encoding.

    Args:
        video_path: Path to the video-only file.
        audio_path: Path to the audio-only file.
        output_path: Path for the merged output.

    Returns:
        Path to the merged file.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    settings = get_settings()
    ffmpeg = settings.ffmpeg_path

    cmd = [
        ffmpeg,
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path,
    ]

    logger.info("Merging: {} + {} -> {}", video_path, audio_path, output_path)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
        logger.error("FFmpeg merge failed: {}", error_msg)
        raise RuntimeError(f"FFmpeg merge failed: {error_msg}")

    if not Path(output_path).exists():
        raise RuntimeError("FFmpeg merge completed but output file not found")

    logger.info("Merge complete: {}", output_path)
    return output_path

"""FFmpeg audio converter.

Converts audio files to MP3 format.
"""

import asyncio
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings


async def convert_to_mp3(
    input_path: str,
    output_path: str,
    bitrate: str = "320K",
) -> str:
    """Convert an audio file to MP3 using FFmpeg.

    Args:
        input_path: Path to the source audio file.
        output_path: Path for the MP3 output.
        bitrate: Audio bitrate (default: 320K).

    Returns:
        Path to the converted file.

    Raises:
        RuntimeError: If FFmpeg conversion fails.
    """
    settings = get_settings()
    ffmpeg = settings.ffmpeg_path

    cmd = [
        ffmpeg,
        "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", bitrate,
        "-ar", "44100",
        "-q:a", "0",
        output_path,
    ]

    logger.info("Converting to MP3: {} -> {}", input_path, output_path)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
        logger.error("FFmpeg conversion failed: {}", error_msg)
        raise RuntimeError(f"FFmpeg conversion failed: {error_msg}")

    if not Path(output_path).exists():
        raise RuntimeError("FFmpeg conversion completed but output file not found")

    logger.info("Conversion complete: {}", output_path)
    return output_path

"""Audio download service.

Handles downloading YouTube audio as MP3 using yt-dlp + FFmpeg.
"""

import asyncio
from pathlib import Path
from typing import Callable

import yt_dlp
from loguru import logger

from app.config.settings import get_settings
from app.services.ffmpeg.converter import convert_to_mp3
from app.utils.file_utils import get_safe_filepath


class AudioDownloader:
    """Downloads YouTube audio tracks as MP3."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def download(
        self,
        url: str,
        format_id: str,
        video_id: str,
        title: str,
        on_progress: Callable[[str], None] | None = None,
        cancel_event: asyncio.Event | None = None,
    ) -> Path:
        """Download audio and convert to MP3.

        Args:
            url: YouTube URL.
            format_id: yt-dlp format ID for the audio stream.
            video_id: 11-char YouTube video ID.
            title: Video title for filename.
            on_progress: Callback for status messages.
            cancel_event: Event to signal cancellation.

        Returns:
            Path to the final MP3 file.
        """
        download_dir = self.settings.download_dir / video_id
        download_dir.mkdir(parents=True, exist_ok=True)

        if on_progress:
            on_progress("Downloading audio...")

        ydl_opts = {
            "format": format_id,
            "outtmpl": str(download_dir / "audio.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        loop = asyncio.get_event_loop()

        def _run_download() -> None:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, _run_download)

        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError()

        # Find the downloaded audio file
        audio_source = None
        for f in download_dir.iterdir():
            if f.stem == "audio":
                audio_source = f
                break

        if audio_source is None:
            raise FileNotFoundError("Audio download failed - no file found")

        # Convert to MP3
        if on_progress:
            on_progress("Converting to MP3...")

        output_path = get_safe_filepath(
            self.settings.download_dir, title, ".mp3"
        )

        await convert_to_mp3(
            input_path=str(audio_source),
            output_path=str(output_path),
        )

        # Cleanup
        audio_source.unlink(missing_ok=True)
        download_dir.rmdir()

        logger.info("Audio download complete: {}", output_path.name)
        return output_path

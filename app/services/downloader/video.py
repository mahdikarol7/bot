"""Video download service.

Handles downloading YouTube videos using yt-dlp with progress tracking.
Merges video + audio with FFmpeg when they're separate streams.
"""

import asyncio
from pathlib import Path
from typing import Callable

import yt_dlp
from loguru import logger

from app.config.settings import get_settings
from app.services.ffmpeg.merger import merge_audio_video
from app.utils.file_utils import get_safe_filepath


class VideoDownloader:
    """Downloads YouTube videos with progress callbacks."""

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
        """Download a video and merge with audio if needed.

        Args:
            url: YouTube URL.
            format_id: yt-dlp format ID for the video stream.
            video_id: 11-char YouTube video ID.
            title: Video title for filename.
            on_progress: Callback for status messages.
            cancel_event: Event to signal cancellation.

        Returns:
            Path to the final merged MP4 file.

        Raises:
            yt_dlp.utils.DownloadError: If download fails.
            asyncio.CancelledError: If cancelled.
        """
        download_dir = self.settings.download_dir / video_id
        download_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Download video-only stream
        if on_progress:
            on_progress("Downloading video...")

        video_path = await self._download_format(
            url=url,
            format_id=format_id,
            output_dir=download_dir,
            filename="video",
            cancel_event=cancel_event,
        )

        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError()

        # Step 2: Download best audio stream
        if on_progress:
            on_progress("Downloading audio...")

        audio_path = await self._download_format(
            url=url,
            format_id="bestaudio",
            output_dir=download_dir,
            filename="audio",
            cancel_event=cancel_event,
        )

        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError()

        # Step 3: Merge video + audio
        if on_progress:
            on_progress("Merging audio and video...")

        output_path = get_safe_filepath(
            self.settings.download_dir, title, ".mp4"
        )

        await merge_audio_video(
            video_path=str(video_path),
            audio_path=str(audio_path),
            output_path=str(output_path),
        )

        # Cleanup temp files
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        download_dir.rmdir()

        logger.info("Video download complete: {}", output_path.name)
        return output_path

    async def _download_format(
        self,
        url: str,
        format_id: str,
        output_dir: Path,
        filename: str,
        cancel_event: asyncio.Event | None = None,
    ) -> Path:
        """Download a single format using yt-dlp."""
        output_template = str(output_dir / f"{filename}.%(ext)s")

        ydl_opts = {
            "format": format_id,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "progress_hooks": [],
            # Anti-bot settings
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android"],
                    "player_skip": ["webpage"],
                }
            },
        }

        # Add cookies if file exists
        cookies_file = Path("cookies.txt")
        if cookies_file.exists():
            ydl_opts["cookiefile"] = str(cookies_file)

        loop = asyncio.get_event_loop()

        def _run_download() -> None:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, _run_download)

        # Find the downloaded file
        for f in output_dir.iterdir():
            if f.stem == filename:
                return f

        raise FileNotFoundError(f"Downloaded file not found in {output_dir}")

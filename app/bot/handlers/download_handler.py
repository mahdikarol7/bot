"""Download handler.

Processes download type and quality selections, manages the download lifecycle.
"""

import asyncio
from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, InputFile
from loguru import logger

from app.bot.keyboards.inline import (
    get_video_quality_keyboard,
    get_audio_quality_keyboard,
)
from app.bot.states.download import DownloadStates
from app.cache.file_cache import FileCache
from app.config.settings import get_settings
from app.database.models.download import DownloadStatus, DownloadType
from app.database.repositories.download_repo import DownloadRepository
from app.services.downloader.audio import AudioDownloader
from app.services.downloader.video import VideoDownloader
from app.services.youtube.metadata import (
    extract_metadata,
    get_available_video_qualities,
    get_available_audio_qualities,
)
from app.utils.file_utils import TELEGRAM_MAX_FILE_SIZE, delete_file

router = Router(name="download_handler")
file_cache = FileCache()


@router.callback_query(F.data.startswith("type_"), DownloadStates.choosing_type)
async def handle_download_type(callback: CallbackQuery, state) -> None:
    """Handle Video or Audio type selection."""
    await callback.answer()

    data = await state.get_data()
    metadata = data.get("metadata")
    url = data.get("url")
    video_id = data.get("video_id")

    if not metadata or not url:
        await callback.message.edit_text("❌ Session expired. Please send the URL again.")
        await state.clear()
        return

    download_type = callback.data.replace("type_", "")

    if download_type == "video":
        qualities = get_available_video_qualities(metadata)
        if not qualities:
            await callback.message.edit_text(
                "❌ No supported video qualities found for this video."
            )
            await state.clear()
            return

        # Check if "Best Quality" option should be added
        has_best = any(q["resolution"] == "1080p" for q in qualities)

        await state.update_data(download_type="video", video_qualities=qualities)
        await callback.message.edit_text(
            f"🎥 Choose video quality for:\n{metadata.title}",
            reply_markup=get_video_quality_keyboard(qualities),
        )
        await state.set_state(DownloadStates.choosing_quality)

    elif download_type == "audio":
        qualities = get_available_audio_qualities(metadata)
        if not qualities:
            # Fallback: offer download with best audio
            qualities = [{"format_id": "bestaudio", "quality": "Best Audio", "abr": 0}]

        await state.update_data(download_type="audio", audio_qualities=qualities)
        await callback.message.edit_text(
            f"🎵 Choose audio quality for:\n{metadata.title}",
            reply_markup=get_audio_quality_keyboard(qualities),
        )
        await state.set_state(DownloadStates.choosing_quality)


@router.callback_query(F.data.startswith("vq:"), DownloadStates.choosing_quality)
async def handle_video_quality(callback: CallbackQuery, state) -> None:
    """Handle video quality selection and start download."""
    await callback.answer()

    data = await state.get_data()
    url = data.get("url")
    video_id = data.get("video_id")
    title = data.get("title", "video")
    qualities = data.get("video_qualities", [])

    format_id = callback.data.removeprefix("vq:")

    # Find the selected quality info
    selected = next((q for q in qualities if q["format_id"] == format_id), None)
    quality_label = selected["resolution"] if selected else "unknown"

    settings = get_settings()

    # Check cache first
    cached = file_cache.get_cached_file(video_id, "video", quality_label)
    if cached:
        await callback.message.edit_text("⚡ Serving from cache...")
        await _send_file(callback, cached, settings)
        await state.clear()
        return

    # Create download record
    session = data.get("session")
    repo = DownloadRepository(session) if session else None
    download_record = None
    if repo:
        download_record = await repo.create(
            user_telegram_id=callback.from_user.id,
            youtube_url=url,
            download_type=DownloadType.VIDEO,
            quality=quality_label,
            title=title,
        )

    # Start download
    await state.set_state(DownloadStates.downloading)
    status_msg = await callback.message.edit_text("⏳ Starting download...")

    cancel_event = asyncio.Event()
    downloader = VideoDownloader()

    def on_progress(msg: str) -> None:
        asyncio.create_task(status_msg.edit_text(f"⏳ {msg}"))

    try:
        filepath = await downloader.download(
            url=url,
            format_id=format_id,
            video_id=video_id,
            title=title,
            on_progress=on_progress,
            cancel_event=cancel_event,
        )

        # Check file size
        file_size = filepath.stat().st_size
        if file_size > TELEGRAM_MAX_FILE_SIZE:
            await status_msg.edit_text(
                "❌ This quality is too large to upload.\n"
                "Please choose a lower quality."
            )
            await delete_file(filepath)
            if repo and download_record:
                await repo.update_status(
                    download_record.id, DownloadStatus.FAILED,
                    error_message="File too large"
                )
            await state.clear()
            return

        # Cache the file
        cache_path = file_cache.get_cache_path(video_id, "video", quality_label)
        import shutil
        shutil.copy2(str(filepath), str(cache_path))

        # Send to user
        await status_msg.edit_text("⬆️ Uploading to Telegram...")
        await _send_file(callback, filepath, settings)

        # Update record
        if repo and download_record:
            await repo.update_status(
                download_record.id, DownloadStatus.COMPLETED,
                file_path=str(filepath),
                file_size=file_size,
            )

        # Cleanup temp file (cache copy is kept)
        await delete_file(filepath)
        await status_msg.delete()

    except asyncio.CancelledError:
        await status_msg.edit_text("❌ Download cancelled.")
        if repo and download_record:
            await repo.update_status(download_record.id, DownloadStatus.CANCELLED)
    except Exception as e:
        logger.error("Download failed: {}", e)
        await status_msg.edit_text(
            "❌ Download failed. Please try again later."
        )
        if repo and download_record:
            await repo.update_status(
                download_record.id, DownloadStatus.FAILED,
                error_message=str(e),
            )

    await state.clear()


@router.callback_query(F.data.startswith("aq:"), DownloadStates.choosing_quality)
async def handle_audio_quality(callback: CallbackQuery, state) -> None:
    """Handle audio quality selection and start download."""
    await callback.answer()

    data = await state.get_data()
    url = data.get("url")
    video_id = data.get("video_id")
    title = data.get("title", "audio")
    qualities = data.get("audio_qualities", [])

    format_id = callback.data.removeprefix("aq:")

    selected = next((q for q in qualities if q["format_id"] == format_id), None)
    quality_label = selected["quality"] if selected else "best"

    settings = get_settings()

    # Check cache
    cached = file_cache.get_cached_file(video_id, "audio", quality_label)
    if cached:
        await callback.message.edit_text("⚡ Serving from cache...")
        await _send_file(callback, cached, settings)
        await state.clear()
        return

    # Create download record
    session = data.get("session")
    repo = DownloadRepository(session) if session else None
    download_record = None
    if repo:
        download_record = await repo.create(
            user_telegram_id=callback.from_user.id,
            youtube_url=url,
            download_type=DownloadType.AUDIO,
            quality=quality_label,
            title=title,
        )

    await state.set_state(DownloadStates.downloading)
    status_msg = await callback.message.edit_text("⏳ Starting download...")

    cancel_event = asyncio.Event()
    downloader = AudioDownloader()

    def on_progress(msg: str) -> None:
        asyncio.create_task(status_msg.edit_text(f"⏳ {msg}"))

    try:
        filepath = await downloader.download(
            url=url,
            format_id=format_id,
            video_id=video_id,
            title=title,
            on_progress=on_progress,
            cancel_event=cancel_event,
        )

        file_size = filepath.stat().st_size

        # Cache the file
        cache_path = file_cache.get_cache_path(video_id, "audio", quality_label)
        import shutil
        shutil.copy2(str(filepath), str(cache_path))

        await status_msg.edit_text("⬆️ Uploading to Telegram...")
        await _send_file(callback, filepath, settings)

        if repo and download_record:
            await repo.update_status(
                download_record.id, DownloadStatus.COMPLETED,
                file_path=str(filepath),
                file_size=file_size,
            )

        await delete_file(filepath)
        await status_msg.delete()

    except asyncio.CancelledError:
        await status_msg.edit_text("❌ Download cancelled.")
        if repo and download_record:
            await repo.update_status(download_record.id, DownloadStatus.CANCELLED)
    except Exception as e:
        logger.error("Audio download failed: {}", e)
        await status_msg.edit_text(
            "❌ Download failed. Please try again later."
        )
        if repo and download_record:
            await repo.update_status(
                download_record.id, DownloadStatus.FAILED,
                error_message=str(e),
            )

    await state.clear()


async def _send_file(
    callback: CallbackQuery, filepath: Path, settings
) -> None:
    """Send a file to the user via Telegram."""
    file_size = filepath.stat().st_size
    if file_size > settings.max_file_size_bytes:
        await callback.message.answer(
            "❌ File is too large for Telegram upload."
        )
        return

    if filepath.suffix == ".mp3":
        from aiogram.types import FSInputFile
        await callback.message.answer_audio(
            audio=FSInputFile(str(filepath)),
        )
    else:
        from aiogram.types import FSInputFile
        await callback.message.answer_video(
            video=FSInputFile(str(filepath)),
        )

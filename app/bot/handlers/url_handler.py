"""YouTube URL handler.

Processes incoming YouTube URLs, extracts metadata, and shows options.
"""

from aiogram import Router
from aiogram.types import Message
from loguru import logger

from app.bot.filters.url_filter import YouTubeURLFilter
from app.bot.keyboards.inline import get_download_type_keyboard
from app.bot.states.download import DownloadStates
from app.services.youtube.metadata import extract_metadata
from app.utils.file_utils import format_views

router = Router(name="url_handler")


@router.message(YouTubeURLFilter())
async def handle_youtube_url(message: Message, state) -> None:
    """Handle a YouTube URL sent by the user."""
    url = message.text.strip()

    # Show loading message
    loading_msg = await message.answer("⏳ Fetching video information...")

    try:
        metadata = await extract_metadata(url)
    except Exception as e:
        logger.error("Failed to extract metadata: {}", e)
        error_text = str(e).lower()
        if "private" in error_text:
            text = "🔒 This video is private."
        elif "unavailable" in error_text or "removed" in error_text:
            text = "🚫 This video is unavailable or has been removed."
        elif "age" in error_text:
            text = "🔞 This video has age restrictions."
        elif "region" in error_text:
            text = "🌍 This video is not available in your region."
        else:
            text = "❌ Failed to fetch video info. Please check the URL."
        await loading_msg.edit_text(text)
        return

    # Build info caption
    caption = (
        f"📺 {metadata.title}\n\n"
        f"👤 {metadata.channel}\n"
        f"⏱ {metadata.duration_formatted}\n"
        f"👁 {format_views(metadata.view_count)} views"
    )

    # Store metadata in state data
    await state.set_data({
        "url": url,
        "video_id": metadata.video_id,
        "title": metadata.title,
        "metadata": metadata,
    })

    # Show thumbnail with options
    if metadata.thumbnail:
        try:
            from aiogram.types import URLInputFile
            photo = URLInputFile(metadata.thumbnail)
            await loading_msg.delete()
            await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=get_download_type_keyboard(),
            )
        except Exception:
            await loading_msg.edit_text(
                text=caption,
                reply_markup=get_download_type_keyboard(),
            )
    else:
        await loading_msg.edit_text(
            text=caption,
            reply_markup=get_download_type_keyboard(),
        )

    await state.set_state(DownloadStates.choosing_type)

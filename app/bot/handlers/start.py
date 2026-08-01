"""Start and help command handlers."""

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    await message.answer(
        "👋 Welcome to YouTube Downloader Bot!\n\n"
        "Just send me a YouTube link and I'll help you download it.\n\n"
        "📌 Supported:\n"
        "• YouTube Videos\n"
        "• YouTube Shorts\n\n"
        "Type /help for more information."
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        "📖 How to use this bot:\n\n"
        "1️⃣ Send a YouTube URL\n"
        "2️⃣ Choose Video or Audio\n"
        "3️⃣ Select quality\n"
        "4️⃣ Wait for download\n\n"
        "🎥 Video qualities: 360p, 480p, 720p, 1080p\n"
        "🎵 Audio qualities: 128k, 192k, 320k, Best\n\n"
        "⚠️ Telegram file size limit: 2GB\n"
        "💡 Cached downloads are served instantly!"
    )

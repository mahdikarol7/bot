"""Admin command handlers."""

import os
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.filters.admin_filter import IsAdminFilter
from app.cache.file_cache import FileCache
from app.config.settings import get_settings
from app.database.repositories.download_repo import DownloadRepository
from app.database.repositories.user_repo import UserRepository
from app.utils.file_utils import format_file_size

router = Router(name="admin")
file_cache = FileCache()


@router.message(Command("admin"), IsAdminFilter())
async def cmd_admin(message: Message, session) -> None:
    """Show admin panel."""
    settings = get_settings()
    user_repo = UserRepository(session)
    download_repo = DownloadRepository(session)

    total_users = await user_repo.get_total_users()
    total_downloads = await download_repo.get_total_downloads()
    cache_size = file_cache.get_cache_size()

    # Disk usage
    download_dir = settings.download_dir
    disk_usage = sum(
        f.stat().st_size for f in download_dir.rglob("*") if f.is_file()
    ) if download_dir.exists() else 0

    text = (
        "🔧 Admin Panel\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📥 Total Downloads: {total_downloads}\n"
        f"💾 Cache Size: {format_file_size(cache_size)}\n"
        f"📂 Downloads Disk: {format_file_size(disk_usage)}\n"
    )

    await message.answer(text)


@router.message(Command("broadcast"), IsAdminFilter())
async def cmd_broadcast(message: Message, user_repo: UserRepository) -> None:
    """Broadcast a message to all users."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /broadcast <message>")
        return

    broadcast_text = parts[1]
    users = await user_repo.get_all_users()
    sent = 0
    failed = 0

    await message.answer(f"📢 Broadcasting to {len(users)} users...")

    for user in users:
        try:
            from aiogram import Bot
            from app.config.settings import get_settings
            bot = Bot(token=get_settings().bot_token)
            await bot.send_message(chat_id=user.telegram_id, text=broadcast_text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Sent: {sent}\n❌ Failed: {failed}")


@router.message(Command("clearcache"), IsAdminFilter())
async def cmd_clear_cache(message: Message) -> None:
    """Clear all cached files."""
    count = file_cache.clear_cache()
    await message.answer(f"🗑 Cache cleared: {count} files removed.")

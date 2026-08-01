"""YouTube Downloader Bot - Entry Point.

This module initializes and runs the Telegram bot.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings
from app.database.db import init_db, close_db, async_session_factory
from app.bot.setup import create_bot, create_dispatcher


def setup_logging() -> None:
    """Configure Loguru logging."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console output
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True,
    )

    # File output
    log_file = settings.log_dir / "bot.log"
    logger.add(
        str(log_file),
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
               "{name}:{function}:{line} - {message}",
    )


def setup_cookies() -> None:
    """Write cookies.txt from COOKIES_CONTENT environment variable."""
    import os
    cookies_content = os.environ.get("COOKIES_CONTENT", "")
    if cookies_content:
        cookies_file = Path("cookies.txt")
        cookies_file.write_text(cookies_content, encoding="utf-8")
        logger.info("YouTube cookies loaded from environment variable")
    elif Path("cookies.txt").exists():
        logger.info("Using existing cookies.txt file")
    else:
        logger.warning("No cookies found - YouTube may block requests")


async def main() -> None:
    """Main entry point for the bot."""
    settings = get_settings()
    settings.ensure_directories()

    setup_logging()
    logger.info("Starting YouTube Downloader Bot...")

    # Setup YouTube cookies
    setup_cookies()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher(async_session_factory)

    try:
        # Start polling
        logger.info("Bot is now polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
        )
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

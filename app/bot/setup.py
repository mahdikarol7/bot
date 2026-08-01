"""Bot setup and router registration.

Configures the Aiogram bot with all handlers, middlewares, and routers.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.handlers import (
    admin_handler,
    cancel_handler,
    download_handler,
    start,
    url_handler,
)
from app.bot.middlewares.database import DatabaseMiddleware
from app.bot.middlewares.rate_limit import RateLimitMiddleware
from app.bot.states.download import DownloadStates
from app.config.settings import get_settings


def create_bot() -> Bot:
    """Create and configure the Aiogram Bot instance."""
    settings = get_settings()
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(session_factory: async_sessionmaker) -> Dispatcher:
    """Create and configure the Aiogram Dispatcher."""
    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(DatabaseMiddleware(session_factory))
    dp.callback_query.middleware(DatabaseMiddleware(session_factory))
    dp.message.middleware(RateLimitMiddleware())

    # Register routers (order matters!)
    dp.include_router(start.router)
    dp.include_router(admin_handler.router)
    dp.include_router(download_handler.router)
    dp.include_router(url_handler.router)
    dp.include_router(cancel_handler.router)

    # Set initial state for URL handling
    dp.startup.register(_on_startup)

    return dp


async def _on_startup(dispatcher: Dispatcher) -> None:
    """Set initial FSM state."""
    await dispatcher.storage.set_state(
        state=DownloadStates.waiting_for_url,
    )

"""Database middleware.

Provides a database session for each request and ensures user records exist.
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.repositories.user_repo import UserRepository


class DatabaseMiddleware(BaseMiddleware):
    """Middleware that provides database session and user repo."""

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def __call__(self, handler, event, data: dict) -> None:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            data["session"] = session
            data["user_repo"] = user_repo

            # Auto-register user
            user = event.from_user
            if user:
                await user_repo.create_or_update(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                )

            return await handler(event, data)

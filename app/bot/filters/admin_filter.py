"""Admin filter for commands."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.config.settings import get_settings


class IsAdminFilter(BaseFilter):
    """Filter that checks if the user is a configured admin."""

    async def __call__(self, message: Message) -> bool:
        settings = get_settings()
        if not settings.admin_telegram_id:
            return False
        return message.from_user is not None and (
            message.from_user.id == settings.admin_telegram_id
        )

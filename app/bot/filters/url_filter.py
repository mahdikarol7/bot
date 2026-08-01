"""URL filter for incoming messages."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

from app.utils.url_validator import is_valid_youtube_url


class YouTubeURLFilter(BaseFilter):
    """Filter that matches messages containing a valid YouTube URL."""

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return is_valid_youtube_url(message.text.strip())

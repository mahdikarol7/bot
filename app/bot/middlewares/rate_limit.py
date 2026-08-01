"""Rate limiting middleware.

Prevents user spam by limiting requests per time window.
"""

import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message

from app.config.settings import get_settings


class RateLimitMiddleware(BaseMiddleware):
    """Middleware that rate-limits messages per user."""

    def __init__(self) -> None:
        self._user_timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(self, handler, event: Message, data: dict) -> None:
        settings = get_settings()
        user_id = event.from_user.id if event.from_user else 0
        now = time.time()
        window = settings.rate_limit_window_seconds
        max_requests = settings.rate_limit_per_user

        # Clean old timestamps
        self._user_timestamps[user_id] = [
            t for t in self._user_timestamps[user_id] if now - t < window
        ]

        if len(self._user_timestamps[user_id]) >= max_requests:
            if event.text:
                await event.answer(
                    "⏳ Too many requests. Please wait a moment."
                )
            return

        self._user_timestamps[user_id].append(now)
        return await handler(event, data)

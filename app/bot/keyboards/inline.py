"""Inline keyboards for the bot."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_download_type_keyboard() -> InlineKeyboardMarkup:
    """Show Video / Audio / Cancel buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎥 Download Video", callback_data="type_video"),
                InlineKeyboardButton(text="🎵 Download Audio", callback_data="type_audio"),
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
            ],
        ]
    )


def get_video_quality_keyboard(qualities: list[dict]) -> InlineKeyboardMarkup:
    """Show available video quality buttons."""
    buttons: list[list[InlineKeyboardButton]] = []
    for q in qualities:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🎥 {q['resolution']}",
                    callback_data=f"vq:{q['format_id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_audio_quality_keyboard(qualities: list[dict]) -> InlineKeyboardMarkup:
    """Show available audio quality buttons."""
    buttons: list[list[InlineKeyboardButton]] = []
    for q in qualities:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🎵 {q['quality']}",
                    callback_data=f"aq:{q['format_id']}",
                )
            ]
        )
    buttons.append(
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
        ]
    )


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm / Cancel buttons."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="confirm"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
            ]
        ]
    )

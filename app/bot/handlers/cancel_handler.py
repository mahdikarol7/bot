"""Cancel handler for download flow."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.bot.states.download import DownloadStates

router = Router(name="cancel_handler")


@router.callback_query(F.data == "cancel", DownloadStates.choosing_type)
@router.callback_query(F.data == "cancel", DownloadStates.choosing_quality)
@router.callback_query(F.data == "cancel", DownloadStates.downloading)
async def handle_cancel(callback: CallbackQuery, state) -> None:
    """Handle cancel button press."""
    await callback.answer()
    await callback.message.edit_text("❌ Cancelled.")
    await state.clear()


@router.callback_query(F.data == "cancel")
async def handle_cancel_any(callback: CallbackQuery, state) -> None:
    """Handle cancel in any state."""
    await callback.answer()
    try:
        await callback.message.edit_text("❌ Cancelled.")
    except Exception:
        await callback.message.answer("❌ Cancelled.")
    await state.clear()

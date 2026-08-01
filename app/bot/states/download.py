"""FSM states for the download flow."""

from aiogram.fsm.state import State, StatesGroup


class DownloadStates(StatesGroup):
    """States for the download conversation flow."""

    waiting_for_url = State()
    choosing_type = State()
    choosing_quality = State()
    downloading = State()

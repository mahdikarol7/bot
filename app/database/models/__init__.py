"""Database models package."""

from app.database.models.user import UserModel
from app.database.models.download import DownloadModel

__all__ = ["UserModel", "DownloadModel"]

"""Download database model."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class DownloadStatus(str):
    """Download status constants."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadType(str):
    """Download type constants."""
    VIDEO = "video"
    AUDIO = "audio"


class DownloadModel(Base):
    """Represents a download request."""

    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    youtube_url: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    download_type: Mapped[str] = mapped_column(
        Enum(DownloadType, native_enum=False), nullable=False
    )
    quality: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(DownloadStatus, native_enum=False),
        default=DownloadStatus.PENDING,
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Download {self.id} ({self.status})>"

"""Download repository for database operations."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.download import DownloadModel, DownloadStatus


class DownloadRepository:
    """Handles download CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_telegram_id: int,
        youtube_url: str,
        download_type: str,
        quality: str,
        title: str | None = None,
    ) -> DownloadModel:
        """Create a new download record."""
        download = DownloadModel(
            user_telegram_id=user_telegram_id,
            youtube_url=youtube_url,
            download_type=download_type,
            quality=quality,
            title=title,
            status=DownloadStatus.PENDING,
        )
        self.session.add(download)
        await self.session.commit()
        return download

    async def update_status(
        self,
        download_id: int,
        status: str,
        file_path: str | None = None,
        file_size: int | None = None,
        error_message: str | None = None,
    ) -> DownloadModel | None:
        """Update download status and optional fields."""
        stmt = select(DownloadModel).where(DownloadModel.id == download_id)
        result = await self.session.execute(stmt)
        download = result.scalar_one_or_none()
        if download:
            download.status = status
            if file_path is not None:
                download.file_path = file_path
            if file_size is not None:
                download.file_size = file_size
            if error_message is not None:
                download.error_message = error_message
            if status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED):
                download.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
        return download

    async def get_total_downloads(self) -> int:
        """Return total number of downloads."""
        stmt = select(func.count(DownloadModel.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_by_user(self, user_telegram_id: int) -> list[DownloadModel]:
        """Return all downloads for a user."""
        stmt = (
            select(DownloadModel)
            .where(DownloadModel.user_telegram_id == user_telegram_id)
            .order_by(DownloadModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

"""User repository for database operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import UserModel


class UserRepository:
    """Handles user CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> UserModel | None:
        """Fetch a user by their Telegram ID."""
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> UserModel:
        """Create a new user or update existing one."""
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = UserModel(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            self.session.add(user)
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        await self.session.commit()
        return user

    async def increment_downloads(self, telegram_id: int) -> None:
        """Increment download count for a user."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.total_downloads += 1
            await self.session.commit()

    async def get_total_users(self) -> int:
        """Return total number of users."""
        stmt = select(func.count(UserModel.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if a user is admin."""
        user = await self.get_by_telegram_id(telegram_id)
        return user.is_admin if user else False

    async def get_all_users(self) -> list[UserModel]:
        """Return all users."""
        stmt = select(UserModel)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

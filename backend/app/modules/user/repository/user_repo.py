from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.user.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_user(self, name: str) -> User:
        user = User(name=name)
        self._session.add(user)
        await self._session.refresh()
        return user

    async def get_user(
        self, user_id: UUID, is_active: bool | None = None
    ) -> User | None:
        stmt = (
            select(User)
            .where(
                User.id == user_id,
            )
            .options(selectinload(User.auth_identities))
        )
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

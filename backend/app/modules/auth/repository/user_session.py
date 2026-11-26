from datetime import datetime
from uuid import UUID

from app.modules.auth.models.user_session import UserSession
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


class UserSessionRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_session(
        self, user_id: UUID, refresh_token_hash, expires_at: datetime
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
        )
        self._session.add(user_session)
        await self._session.refresh()
        return user_session

    async def get_session_by_refresh(
        self, refresh_token_hash: str
    ) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == refresh_token_hash
        )
        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()

    async def update_refresh_token(
        self,
        user_session_id: UUID,
        new_refresh_token_hash: str,
        old_refresh_token_hash: str,
    ) -> UserSession:
        stmt = (
            update(UserSession)
            .where(
                UserSession.id == user_session_id,
                UserSession.refresh_token_hash == old_refresh_token_hash,
            )
            .values(refresh_token_hash=new_refresh_token_hash)
        ).returning(UserSession)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_session_id: UUID) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.id == user_session_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session(
        self, user_session_id: UUID, revoked_at: datetime
    ) -> UserSession | None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == user_session_id)
            .values(revoked_at=revoked_at)
        ).returning(UserSession)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_all_sessions(
        self, user_id: UUID, revoked_at: datetime
    ) -> list[UserSession]:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        ).returning(UserSession)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_active_session(
        self, user_session_id: UUID, user_id: UUID
    ) -> UserSession | None:
        stmt = select(UserSession).where(
            UserSession.id == user_session_id, UserSession.user_id == user_id
        )
        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()

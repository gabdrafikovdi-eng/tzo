from datetime import datetime
from uuid import UUID

from app.modules.auth.models.user_session import UserSession
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
        self._session.add()
        await self._session.refresh()
        return user_session

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import get_settings
from app.modules.auth.repository.user_session import UserSessionRepo
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth.dto.user_session import UserSessionDTO


class SessionService:
    def __init__(self, session: AsyncSession):

        self._user_session_repo = UserSessionRepo(session=session)
        self._settings = get_settings()

    async def create_session(self, user_id: UUID, refresh_token: str) -> UserSessionDTO:
        session = await self._user_session_repo.create_session(
            user_id=user_id,
            refresh_token_hash=self._token_service.hash_refresh_token(
                token=refresh_token
            ),
            expires_at=datetime.now(UTC)
            + timedelta.days(self._settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return UserSessionDTO(
            id=session.id,
            user_id=session.user_id,
            refresh_token_hash=session.refresh_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

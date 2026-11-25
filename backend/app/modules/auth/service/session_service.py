from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import get_settings
from app.modules.auth.repository.user_session import UserSessionRepo
from app.modules.auth.service.token_service import TokenService
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth.models.user_session import UserSession


class SessionService:
    def __init__(self, token_service: TokenService, session: AsyncSession):
        self._token_service = token_service
        self._user_session_repo = UserSessionRepo(session=session)
        self._settings = get_settings()

    async def create_session(self, user_id: UUID) -> UserSession:
        refresh_token = self._token_service.create_refresh_token()

        session = await self._user_session_repo.create_session(
            user_id=user_id,
            refresh_token_hash=self._token_service.hash_refresh_token(
                token=refresh_token
            ),
            expires_at=datetime.now(UTC)
            + timedelta.days(self._settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return session

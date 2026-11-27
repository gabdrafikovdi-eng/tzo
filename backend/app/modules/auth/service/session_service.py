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

    async def create_session(
        self, user_id: UUID, refresh_token_hash: str
    ) -> UserSessionDTO:
        session = await self._user_session_repo.create_session(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(days=self._settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return UserSessionDTO(
            id=session.id,
            user_id=session.user_id,
            refresh_token_hash=session.refresh_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    async def get_session_by_refresh(self, refresh_token_hash: str) -> UserSessionDTO:
        user_session = await self._user_session_repo.get_session(
            refresh_token_hash=refresh_token_hash
        )
        if user_session is None:
            raise  # TODO Нужно будет реализовать ошибку not found user session

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

    async def update_refresh_token(
        self,
        user_session_id: UUID,
        new_refresh_token_hash: str,
        old_refresh_token_hash: str,
    ) -> UserSessionDTO:
        user_session = await self._user_session_repo.update_refresh_token(
            user_session_id=user_session_id,
            new_refresh_token_hash=new_refresh_token_hash,
            old_refresh_token_hash=old_refresh_token_hash,
        )

        if user_session is None:
            current_session = await self._user_session_repo.get_by_id(
                user_session_id=user_session_id
            )

            if current_session is None:
                raise  # TODO  Вернуть ошибку NotFound user session

            if current_session.refresh_token_hash != old_refresh_token_hash:
                return UserSessionDTO(
                    id=current_session.id,
                    user_id=current_session.user_id,
                    refresh_token_hash=current_session.refresh_token_hash,
                    expires_at=current_session.expires_at,
                    revoked_at=current_session.revoked_at,
                )

            raise  # TODO вернуть ошибку не удалось обновить ReplayDetectedError

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

    async def revoke_session(self, user_session_id: UUID, revoked_at: datetime):
        result = await self._user_session_repo.revoke_session(
            user_session_id=user_session_id, revoked_at=revoked_at
        )
        if result is None:
            raise  # TODO Выбросить ошибку что не удалось отозвать сессию

    async def revoke_all_sessions(self, user_id: UUID, revoked_at: datetime):
        await self._user_session_repo.revoke_all_sessions(
            user_id=user_id, revoked_at=revoked_at
        )

    async def get_by_active_session(self, user_session_id: UUID, user_id: UUID):
        user_session = await self._user_session_repo.get_active_session(
            user_session_id=user_session_id, user_id=user_id
        )

        if user_session is None:
            raise  # TODO Выбрасить ошибку что такой сессии нету

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

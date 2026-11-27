from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.modules.auth.dto.user_session import UserSessionDTO
from backend.app.modules.auth.repository.refresh_token import RefreshTokenRepo
from backend.app.modules.auth.repository.user_session import UserSessionRepo


class SessionService:
    def __init__(self, session: AsyncSession):
        self._user_session_repo = UserSessionRepo(session=session)
        self._refresh_token_repo = RefreshTokenRepo(session=session)
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
        await self._refresh_token_repo.create(
            session_id=session.id,
            token_hash=refresh_token_hash,
        )
        return UserSessionDTO(
            id=session.id,
            user_id=session.user_id,
            refresh_token_hash=session.refresh_token_hash,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )

    async def get_session_by_refresh(
        self, refresh_token_hash: str
    ) -> UserSessionDTO | None:
        user_session = await self._user_session_repo.get_session_by_refresh(
            refresh_token_hash=refresh_token_hash
        )
        if user_session is None:
            return None

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

    async def check_replay(self, token_hash: str) -> UUID | None:
        """Возвращает session_id использованного токена или None."""
        token = await self._refresh_token_repo.get_by_hash(token_hash)
        if token is None or token.used_at is None:
            return None
        return token.session_id

    async def update_refresh_token(
        self,
        user_session_id: UUID,
        new_refresh_token_hash: str,
        old_refresh_token_hash: str,
    ) -> UserSessionDTO | None:
        # Сначала пытаемся атомарно обновить сессию.
        # Если UPDATE не затронул строки — значит старый хеш уже не совпадает
        # (replay), сессия отозвана или истекла.
        user_session = await self._user_session_repo.update_refresh_token(
            user_session_id=user_session_id,
            new_refresh_token_hash=new_refresh_token_hash,
            old_refresh_token_hash=old_refresh_token_hash,
        )

        if user_session is None:
            return None

        # Обновление прошло успешно — фиксируем в истории токенов:
        # старый токен помечаем использованным, создаём запись для нового.
        await self._refresh_token_repo.mark_used(old_refresh_token_hash)
        await self._refresh_token_repo.create(
            session_id=user_session_id,
            token_hash=new_refresh_token_hash,
        )

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

    async def revoke_session(
        self, user_session_id: UUID, revoked_at: datetime
    ) -> bool:
        result = await self._user_session_repo.revoke_session(
            user_session_id=user_session_id, revoked_at=revoked_at
        )
        return result is not None

    async def revoke_all_sessions(
        self, user_id: UUID, revoked_at: datetime
    ) -> int:
        result = await self._user_session_repo.revoke_all_sessions(
            user_id=user_id, revoked_at=revoked_at
        )
        return len(result)

    async def get_by_active_session(
        self, user_session_id: UUID, user_id: UUID
    ) -> UserSessionDTO | None:
        user_session = await self._user_session_repo.get_active_session(
            user_session_id=user_session_id, user_id=user_id
        )

        if user_session is None:
            return None

        return UserSessionDTO(
            id=user_session.id,
            user_id=user_session.user_id,
            refresh_token_hash=user_session.refresh_token_hash,
            expires_at=user_session.expires_at,
            revoked_at=user_session.revoked_at,
        )

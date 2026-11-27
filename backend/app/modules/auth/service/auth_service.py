from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.modules.auth.dto.auth_result import AuthResultDTO
from backend.app.modules.auth.dto.token_pair import TokenPairDTO
from backend.app.modules.auth.exceptions import (
    InactiveUserError,
    RefreshTokenReplayError,
    SessionExpiredError,
    SessionNotFoundError,
    SessionRevokedError,
    UnknownRefreshTokenError,
)
from backend.app.modules.auth.providers.telegram import TelegramProvider
from backend.app.modules.auth.service.identity_service import IdentityService
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService


class AuthService:
    def __init__(self, session: AsyncSession):
        self._settings = get_settings()
        self._token_service = TokenService()
        self._telegram = TelegramProvider(
            bot_token=self._settings.TELEGRAM_BOT,
            max_auth_age=self._settings.TELEGRAM_INIT_DATA_EXPIRES,
        )
        self._identity_service = IdentityService(session=session)
        self._session_service = SessionService(session=session)

    async def authenticate_telegram(self, init_data: str) -> AuthResultDTO:
        user_identity = self._telegram.authenticate(init_data=init_data)

        resolved = await self._identity_service.resolve(identity=user_identity)

        if not resolved.user.is_active:
            raise InactiveUserError()

        refresh_token = self._token_service.create_refresh_token()
        refresh_token_hash = self._token_service.hash_refresh_token(refresh_token)
        user_session = await self._session_service.create_session(
            user_id=resolved.user.id, refresh_token_hash=refresh_token_hash
        )
        access_token = self._token_service.create_access_token(
            user_id=resolved.user.id, session_id=user_session.id
        )

        return AuthResultDTO(
            user=resolved.user, access_token=access_token, refresh_token=refresh_token
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPairDTO:
        refresh_token_hash = self._token_service.hash_refresh_token(refresh_token)

        # Проверяем replay: если токен уже был использован ранее — отзываем сессию.
        replay_session_id = await self._session_service.check_replay(refresh_token_hash)
        if replay_session_id is not None:
            await self._session_service.revoke_session(
                user_session_id=replay_session_id, revoked_at=datetime.now(UTC)
            )
            raise RefreshTokenReplayError()

        user_session = await self._session_service.get_session_by_refresh(
            refresh_token_hash=refresh_token_hash
        )
        if user_session is None:
            raise UnknownRefreshTokenError()

        if user_session.revoked_at is not None:
            raise SessionRevokedError()

        now = datetime.now(UTC)
        if user_session.expires_at <= now:
            raise SessionExpiredError()

        new_refresh_token = self._token_service.create_refresh_token()
        new_refresh_token_hash = self._token_service.hash_refresh_token(
            token=new_refresh_token
        )

        updated = await self._session_service.update_refresh_token(
            user_session_id=user_session.id,
            new_refresh_token_hash=new_refresh_token_hash,
            old_refresh_token_hash=refresh_token_hash,
        )

        if updated is None:
            # Конфликт при конкурентном обновлении — строгий replay.
            # Отзываем сессию и отказываем.
            await self._session_service.revoke_session(
                user_session_id=user_session.id, revoked_at=now
            )
            raise RefreshTokenReplayError()

        new_access_token = self._token_service.create_access_token(
            user_id=updated.user_id, session_id=updated.id
        )

        return TokenPairDTO(
            refresh_token=new_refresh_token, access_token=new_access_token
        )

    async def logout(self, refresh_token: str) -> None:
        now = datetime.now(UTC)
        refresh_token_hash = self._token_service.hash_refresh_token(refresh_token)

        user_session = await self._session_service.get_session_by_refresh(
            refresh_token_hash=refresh_token_hash
        )
        if user_session is None:
            raise UnknownRefreshTokenError()

        revoked = await self._session_service.revoke_session(
            user_session_id=user_session.id, revoked_at=now
        )
        if not revoked:
            raise SessionNotFoundError()

    async def all_logout(self, user_id: UUID) -> None:
        now = datetime.now(UTC)
        count = await self._session_service.revoke_all_sessions(
            user_id=user_id, revoked_at=now
        )
        if count == 0:
            raise SessionNotFoundError(message="Активных сессий не найдено")

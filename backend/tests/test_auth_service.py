"""Интеграционные тесты AuthService."""

from datetime import UTC, datetime, timedelta
import asyncio
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.modules.auth.dto.auth_identity import AuthProvider
from backend.app.modules.auth.dto.auth_result import AuthResultDTO
from backend.app.modules.auth.dto.resolved_identity import ResolvedIdentityDTO
from backend.app.modules.auth.dto.token_pair import TokenPairDTO
from backend.app.modules.auth.dto.user_identity import UserIdentityDTO
from backend.app.modules.auth.exceptions import (
    InactiveUserError,
    RefreshTokenReplayError,
    SessionExpiredError,
    SessionRevokedError,
    SessionNotFoundError,
    UnknownRefreshTokenError,
)
from backend.app.modules.auth.models.user_session import UserSession
from backend.app.modules.auth.service.auth_service import AuthService
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.dto.user import UserDTO


class TestAuthServiceAuthenticateTelegram:
    async def test_successful_login_creates_user_and_session(
        self, auth_service: AuthService, test_user_id: UUID
    ):
        resolved = ResolvedIdentityDTO(
            user=UserDTO(id=test_user_id, name="Test", is_active=True),
            identity=None,
        )
        with (
            patch.object(
                auth_service._telegram,
                "authenticate",
                return_value=UserIdentityDTO(
                    provider=AuthProvider.TELEGRAM,
                    external_id="123456789",
                    first_name="Test",
                    last_name="User",
                ),
            ),
            patch.object(
                auth_service._identity_service, "resolve", return_value=resolved
            ),
        ):
            result = await auth_service.authenticate_telegram("fake-init-data")

        assert isinstance(result, AuthResultDTO)
        assert result.user.id == test_user_id
        assert result.access_token
        assert result.refresh_token

    async def test_inactive_user_rejected(
        self, auth_service: AuthService, test_user_id: UUID
    ):
        resolved = ResolvedIdentityDTO(
            user=UserDTO(id=test_user_id, name="Inactive", is_active=False),
            identity=None,
        )
        with (
            patch.object(auth_service._telegram, "authenticate"),
            patch.object(
                auth_service._identity_service, "resolve", return_value=resolved
            ),
        ):
            with pytest.raises(InactiveUserError):
                await auth_service.authenticate_telegram("fake-init-data")


class TestAuthServiceRefreshTokens:
    async def test_concurrent_rotation_only_one_succeeds(
        self,
        auth_service: AuthService,
        session: AsyncSession,
        session_service: SessionService,
        token_service: TokenService,
        test_user_id: UUID,
    ):
        concurrent_old_hash = f"concurrent-old-{uuid4().hex}"
        current = await session_service.create_session(
            user_id=test_user_id, refresh_token_hash=concurrent_old_hash
        )
        refresh_token = token_service.create_refresh_token()
        await session_service.update_refresh_token(
            current.id,
            token_service.hash_refresh_token(refresh_token),
            concurrent_old_hash,
        )
        await session.commit()

        factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)

        async def rotate() -> str:
            async with factory() as concurrent_session:
                await concurrent_session.begin()
                service = AuthService(session=concurrent_session)
                try:
                    result = await service.refresh_tokens(refresh_token)
                except RefreshTokenReplayError:
                    await concurrent_session.commit()
                    return "replay"
                else:
                    await concurrent_session.commit()
                    return result.refresh_token

        results = await asyncio.gather(rotate(), rotate())

        assert sum(result == "replay" for result in results) == 1
        assert sum(result != "replay" for result in results) == 1

    async def test_successful_rotation(
        self,
        auth_service: AuthService,
        session_service: SessionService,
        token_service: TokenService,
        test_user_id: UUID,
    ):
        session = await session_service.create_session(
            user_id=test_user_id, refresh_token_hash="old-hash"
        )
        refresh_token = token_service.create_refresh_token()
        await session_service.update_refresh_token(
            session.id,
            token_service.hash_refresh_token(refresh_token),
            "old-hash",
        )

        result = await auth_service.refresh_tokens(refresh_token)

        assert isinstance(result, TokenPairDTO)
        assert result.refresh_token != refresh_token
        assert result.access_token

    async def test_revoked_token_raises(
        self,
        auth_service: AuthService,
        session_service: SessionService,
        token_service: TokenService,
        test_user_id: UUID,
    ):
        session = await session_service.create_session(
            user_id=test_user_id, refresh_token_hash="old-hash"
        )
        refresh_token = token_service.create_refresh_token()
        await session_service.update_refresh_token(
            session.id,
            token_service.hash_refresh_token(refresh_token),
            "old-hash",
        )
        await session_service.revoke_session(session.id, datetime.now(UTC))

        with pytest.raises(SessionRevokedError):
            await auth_service.refresh_tokens(refresh_token)

    async def test_expired_session_raises(
        self,
        auth_service: AuthService,
        session_service: SessionService,
        token_service: TokenService,
        test_user_id: UUID,
    ):
        session = await session_service.create_session(
            user_id=test_user_id, refresh_token_hash="old-hash"
        )
        refresh_token = token_service.create_refresh_token()
        refresh_hash = token_service.hash_refresh_token(refresh_token)
        await session_service.update_refresh_token(session.id, refresh_hash, "old-hash")
        await session_service._user_session_repo._session.execute(
            update(UserSession)
            .where(UserSession.id == session.id)
            .values(expires_at=datetime.now(UTC) - timedelta(days=1))
        )

        with pytest.raises(SessionExpiredError):
            await auth_service.refresh_tokens(refresh_token)

    async def test_replay_detection_revokes_session(
        self,
        auth_service: AuthService,
        session_service: SessionService,
        token_service: TokenService,
        test_user_id: UUID,
    ):
        session = await session_service.create_session(
            user_id=test_user_id, refresh_token_hash="old-hash"
        )
        refresh_token = token_service.create_refresh_token()
        refresh_hash = token_service.hash_refresh_token(refresh_token)
        await session_service.update_refresh_token(session.id, refresh_hash, "old-hash")
        await auth_service.refresh_tokens(refresh_token)

        with pytest.raises(RefreshTokenReplayError):
            await auth_service.refresh_tokens(refresh_token)

        assert await session_service.get_by_active_session(session.id, test_user_id) is None

    async def test_unknown_token_raises(self, auth_service: AuthService):
        with pytest.raises(UnknownRefreshTokenError):
            await auth_service.refresh_tokens("unknown-token")


class TestAuthServiceLogout:
    async def test_logout_unknown_token(self, auth_service: AuthService):
        with pytest.raises(UnknownRefreshTokenError):
            await auth_service.logout("unknown-token")

    async def test_all_logout_no_sessions(
        self, auth_service: AuthService, test_user_id: UUID
    ):
        with pytest.raises(SessionNotFoundError):
            await auth_service.all_logout(test_user_id)

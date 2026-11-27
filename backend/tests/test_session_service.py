"""Интеграционные тесты для SessionService и репозиториев сессий."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from backend.app.modules.auth.dto.user_session import UserSessionDTO
from backend.app.modules.auth.repository.refresh_token import RefreshTokenRepo
from backend.app.modules.auth.repository.user_session import UserSessionRepo
from backend.app.modules.auth.service.session_service import SessionService


class TestUserSessionRepo:
    async def test_create_and_get_session(
        self,
        user_session_repo: UserSessionRepo,
        test_user_id: UUID,
        sample_refresh_token_hash: str,
    ):
        expires_at = datetime.now(UTC) + timedelta(days=30)

        session = await user_session_repo.create_session(
            user_id=test_user_id,
            refresh_token_hash=sample_refresh_token_hash,
            expires_at=expires_at,
        )

        assert session.id is not None
        assert session.user_id == test_user_id
        assert session.refresh_token_hash == sample_refresh_token_hash
        assert session.expires_at == expires_at
        assert session.revoked_at is None

        fetched = await user_session_repo.get_by_id(session.id)
        assert fetched is not None
        assert fetched.id == session.id
        assert fetched.user_id == test_user_id

    async def test_get_session_by_refresh(
        self,
        user_session_repo: UserSessionRepo,
        test_user_id: UUID,
        sample_refresh_token_hash: str,
    ):
        expires_at = datetime.now(UTC) + timedelta(days=30)

        await user_session_repo.create_session(
            user_id=test_user_id,
            refresh_token_hash=sample_refresh_token_hash,
            expires_at=expires_at,
        )

        found = await user_session_repo.get_session_by_refresh(sample_refresh_token_hash)
        assert found is not None
        assert found.refresh_token_hash == sample_refresh_token_hash
        assert found.user_id == test_user_id

    async def test_get_session_by_refresh_not_found(
        self,
        user_session_repo: UserSessionRepo,
    ):
        found = await user_session_repo.get_session_by_refresh("unknown-hash")
        assert found is None

    async def test_update_refresh_token_success(
        self,
        user_session_repo: UserSessionRepo,
        test_user_id: UUID,
        sample_refresh_token_hash: str,
    ):
        expires_at = datetime.now(UTC) + timedelta(days=30)

        session = await user_session_repo.create_session(
            user_id=test_user_id,
            refresh_token_hash=sample_refresh_token_hash,
            expires_at=expires_at,
        )

        new_hash = "1" * 64
        updated = await user_session_repo.update_refresh_token(
            user_session_id=session.id,
            new_refresh_token_hash=new_hash,
            old_refresh_token_hash=sample_refresh_token_hash,
        )

        assert updated is not None
        assert updated.id == session.id
        assert updated.refresh_token_hash == new_hash

        not_found = await user_session_repo.get_session_by_refresh(sample_refresh_token_hash)
        assert not_found is None

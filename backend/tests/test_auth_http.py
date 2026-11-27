"""HTTP integration tests for the public Auth API.

The tests use the dedicated test database configured in ``conftest.py`` and
remove only the user graph created by each test.
"""

from collections.abc import AsyncGenerator
import json
from uuid import UUID, uuid4

import httpx
import pytest
from init_data_py import sign
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.core.config import get_settings
from backend.app.core.exceptions import AppException
from backend.app.core.session import get_async_session
from backend.app.main import create_app
from backend.app.modules.auth.models.auth_identity import AuthIdentity, AuthProvider
from backend.app.modules.auth.models.refresh_token import RefreshToken
from backend.app.modules.auth.models.user_session import UserSession
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.models.user import User
from backend.app.modules.user.repository.user_repo import UserRepository


async def _delete_user_graph(
    factory: async_sessionmaker[AsyncSession], user_id: UUID
) -> None:
    async with factory() as cleanup_session:
        await cleanup_session.execute(delete(User).where(User.id == user_id))
        await cleanup_session.commit()


def _test_session_dependency(
    factory: async_sessionmaker[AsyncSession],
):
    async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as db_session:
            await db_session.begin()
            try:
                yield db_session
            except AppException as exc:
                if exc.commit_on_error:
                    await db_session.commit()
                else:
                    await db_session.rollback()
                raise
            except BaseException:
                await db_session.rollback()
                raise
            else:
                await db_session.commit()

    return get_test_session


@pytest.mark.asyncio
async def test_refresh_replay_revokes_session_after_http_commit(
    session: AsyncSession,
) -> None:
    """A replay must persist its revocation after the request has ended."""
    factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)
    token_service = TokenService()
    refresh_token = token_service.create_refresh_token()

    async with factory() as seed_session:
        user = await UserRepository(seed_session).create_user(name="HTTP replay")
        user_id = user.id
        created = await SessionService(seed_session).create_session(
            user_id=user_id,
            refresh_token_hash=token_service.hash_refresh_token(refresh_token),
        )
        session_id = created.id
        await seed_session.commit()

    app = create_app()
    app.dependency_overrides[get_async_session] = _test_session_dependency(factory)
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as client:
            first = await client.post(
                "/auth/refresh", headers={"Cookie": f"refresh_token={refresh_token}"}
            )
            assert first.status_code == 200
            replacement = first.json()["access_token"]
            assert replacement

            replay = await client.post(
                "/auth/refresh", headers={"Cookie": f"refresh_token={refresh_token}"}
            )
            assert replay.status_code == 401
            assert replay.json()["error_code"] == "REFRESH_TOKEN_REPLAY"

        # This independent session verifies the committed database state, not
        # the identity-map state that handled the failing request.
        async with factory() as verification_session:
            stored_session = await verification_session.get(UserSession, session_id)
            tokens = (
                await verification_session.scalars(
                    select(RefreshToken).where(RefreshToken.session_id == session_id)
                )
            ).all()
            assert stored_session is not None
            assert stored_session.revoked_at is not None
            assert len(tokens) == 2
            assert all(token.revoked_at is not None for token in tokens)
    finally:
        app.dependency_overrides.clear()
        await _delete_user_graph(factory, user_id)


@pytest.mark.asyncio
async def test_protected_endpoint_and_logout_all_over_http(
    session: AsyncSession,
) -> None:
    factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)
    token_service = TokenService()
    refresh_token = token_service.create_refresh_token()

    async with factory() as seed_session:
        user = await UserRepository(seed_session).create_user(name="HTTP protected")
        user_id = user.id
        created = await SessionService(seed_session).create_session(
            user_id=user_id,
            refresh_token_hash=token_service.hash_refresh_token(refresh_token),
        )
        access_token = token_service.create_access_token(user_id, created.id)
        await seed_session.commit()

    app = create_app()
    app.dependency_overrides[get_async_session] = _test_session_dependency(factory)
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as client:
            current_user = await client.get(
                "/user/me", headers={"Authorization": f"Bearer {access_token}"}
            )
            assert current_user.status_code == 200
            assert current_user.json()["id"] == str(user_id)

            missing_current_user = await client.get("/user/me")
            assert missing_current_user.status_code == 401

            missing = await client.post("/auth/logout-all")
            assert missing.status_code == 401

            invalid = await client.post(
                "/auth/logout-all", headers={"Authorization": "Bearer invalid"}
            )
            assert invalid.status_code == 401

            logged_out = await client.post(
                "/auth/logout-all",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert logged_out.status_code == 204

            refresh = await client.post(
                "/auth/refresh", headers={"Cookie": f"refresh_token={refresh_token}"}
            )
            assert refresh.status_code == 401
            assert refresh.json()["error_code"] == "SESSION_REVOKED"
    finally:
        app.dependency_overrides.clear()
        await _delete_user_graph(factory, user_id)


@pytest.mark.asyncio
async def test_telegram_endpoint_rejects_unverified_init_data(
    session: AsyncSession,
) -> None:
    """Malformed or unsigned Telegram input is never treated as identity data."""
    factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)
    app = create_app()
    app.dependency_overrides[get_async_session] = _test_session_dependency(factory)
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as client:
            response = await client.post(
                "/auth/telegram", json={"init_data": "user=untrusted"}
            )
        assert response.status_code == 401
        assert response.json()["error_code"] == "INVALID_ACCESS_TOKEN"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_telegram_authentication_sets_a_secure_refresh_cookie(
    session: AsyncSession,
) -> None:
    """A valid signed Telegram payload creates an identity through HTTP."""
    factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)
    provider_user_id = str(uuid4().int % 1_000_000_000_000)
    init_data = sign(
        {"user": json.dumps({"id": int(provider_user_id), "first_name": "HTTP"})},
        get_settings().TELEGRAM_BOT,
    )
    app = create_app()
    app.dependency_overrides[get_async_session] = _test_session_dependency(factory)
    transport = httpx.ASGITransport(app=app)
    user_id: UUID | None = None
    try:
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as client:
            response = await client.post("/auth/telegram", json={"init_data": init_data})
        assert response.status_code == 200
        assert response.json()["access_token"]
        cookie = response.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "secure" in cookie
        assert "samesite=lax" in cookie
        assert "path=/auth" in cookie
        assert "max-age=" in cookie

        async with factory() as verification_session:
            identity = await verification_session.scalar(
                select(AuthIdentity).where(
                    AuthIdentity.auth_provider == AuthProvider.TELEGRAM,
                    AuthIdentity.provider_user_id == provider_user_id,
                )
            )
            assert identity is not None
            user_id = identity.user_id
    finally:
        app.dependency_overrides.clear()
        if user_id is not None:
            await _delete_user_graph(factory, user_id)

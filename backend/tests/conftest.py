import asyncio
import os
from datetime import UTC, datetime
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.app.core.config import data_base_conf
from backend.app.modules.auth.dto.user_session import UserSessionDTO
from backend.app.modules.auth.dto.token_pair import TokenPairDTO
from backend.app.modules.auth.repository.auth_identity import AuthIdentityRepo
from backend.app.modules.auth.repository.refresh_token import RefreshTokenRepo
from backend.app.modules.auth.repository.user_session import UserSessionRepo
from backend.app.modules.auth.service.auth_service import AuthService
from backend.app.modules.auth.service.identity_service import IdentityService
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.repository.user_repo import UserRepository
from backend.app.modules.user.service.user_service import UserService

test_database_url = os.getenv("TEST_DATABASE_URL")
if test_database_url is None:
    test_database_url = data_base_conf.DATABASE_URL.rsplit("/", 1)[0] + "/" + (
        data_base_conf.POSTGRES_DB + "-test"
    )

test_engine = create_async_engine(test_database_url, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    bind=test_engine, autoflush=False, expire_on_commit=False
)


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(test_engine.dispose())
    loop.close()


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Создаёт сессию БД с транзакцией, которая откатывается после теста."""
    async with test_session_factory() as sess:
        try:
            yield sess
        finally:
            await sess.rollback()


@pytest_asyncio.fixture
async def user_session_repo(session: AsyncSession) -> UserSessionRepo:
    return UserSessionRepo(session=session)


@pytest_asyncio.fixture
async def refresh_token_repo(session: AsyncSession) -> RefreshTokenRepo:
    return RefreshTokenRepo(session=session)


@pytest_asyncio.fixture
async def auth_identity_repo(session: AsyncSession) -> AuthIdentityRepo:
    return AuthIdentityRepo(session=session)


@pytest_asyncio.fixture
async def user_repo(session: AsyncSession) -> UserRepository:
    return UserRepository(session=session)


@pytest_asyncio.fixture
async def token_service() -> TokenService:
    return TokenService()


@pytest_asyncio.fixture
async def session_service(session: AsyncSession) -> SessionService:
    return SessionService(session=session)


@pytest_asyncio.fixture
async def user_service(session: AsyncSession) -> UserService:
    return UserService(session=session)


@pytest_asyncio.fixture
async def identity_service(session: AsyncSession) -> IdentityService:
    return IdentityService(session=session)


@pytest_asyncio.fixture
async def auth_service(session: AsyncSession) -> AuthService:
    return AuthService(session=session)


@pytest_asyncio.fixture
async def test_user_id(user_repo: UserRepository) -> UUID:
    user = await user_repo.create_user(name="Test user")
    return user.id


@pytest_asyncio.fixture
async def test_session_id() -> UUID:
    return uuid4()


@pytest_asyncio.fixture
async def sample_refresh_token_hash() -> str:
    import hashlib
    return hashlib.sha256(b"test-refresh-token").hexdigest()


@pytest_asyncio.fixture
async def created_session(
    session_service: SessionService,
    sample_refresh_token_hash: str,
    test_user_id: UUID,
) -> UserSessionDTO:
    return await session_service.create_session(
        user_id=test_user_id,
        refresh_token_hash=sample_refresh_token_hash,
    )

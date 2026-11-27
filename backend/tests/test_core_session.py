from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.core import session as session_module
from backend.app.modules.auth.exceptions import InvalidAccessTokenError
from backend.app.modules.user.models.user import User


@pytest.mark.asyncio
async def test_regular_app_exception_rolls_back_transaction(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only errors explicitly marked commit_on_error may commit changes."""
    factory = async_sessionmaker(bind=session.bind, expire_on_commit=False)
    monkeypatch.setattr(session_module, "async_session_factory", factory)
    created_user_id = uuid4()
    dependency = session_module.get_async_session()

    db_session = await anext(dependency)
    db_session.add(User(id=created_user_id, name="must rollback"))
    await db_session.flush()

    with pytest.raises(InvalidAccessTokenError):
        await dependency.athrow(InvalidAccessTokenError())

    async with factory() as verification_session:
        assert await verification_session.get(User, created_user_id) is None


@pytest.mark.asyncio
async def test_commit_failure_is_not_reported_as_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCommitSession:
        async def begin(self) -> None:
            return None

        async def commit(self) -> None:
            raise RuntimeError("commit failed")

        async def rollback(self) -> None:
            return None

    @asynccontextmanager
    async def failing_session_context():
        yield FailingCommitSession()

    monkeypatch.setattr(
        session_module, "async_session_factory", lambda: failing_session_context()
    )
    dependency = session_module.get_async_session()
    await anext(dependency)

    with pytest.raises(RuntimeError, match="commit failed"):
        await anext(dependency)

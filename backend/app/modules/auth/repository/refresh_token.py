from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth.models.refresh_token import RefreshToken


class RefreshTokenRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, session_id: UUID, token_hash: str
    ) -> RefreshToken:
        token = RefreshToken(
            session_id=session_id,
            token_hash=token_hash,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_hash(
        self, token_hash: str
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(
        self, token_hash: str
    ) -> RefreshToken | None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
        ).returning(RefreshToken)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_revoked(
        self, token_hash: str
    ) -> RefreshToken | None:
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        ).returning(RefreshToken)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_session(
        self, session_id: UUID
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.session_id == session_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.used_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
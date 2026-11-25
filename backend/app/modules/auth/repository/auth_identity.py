from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.auth.models.auth_identity import AuthIdentity, AuthProvider


class AuthIdentityRepo:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_auth_identity_by_user_id(
        self, auth_provider: AuthProvider, provider_user_id: str
    ) -> AuthIdentity:
        stmt = (
            select(AuthIdentity)
            .where(
                AuthIdentity.auth_provider == auth_provider,
                AuthIdentity.provider_user_id == provider_user_id,
            )
            .options(selectinload(AuthIdentity.user))
        )
        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()

    async def crate_auth_identity(
        self, user_id: UUID, auth_provider: AuthProvider, provider_user_id: str
    ) -> AuthIdentity:
        new_identity = AuthIdentity(
            user_id=user_id,
            auth_provider=auth_provider,
            provider_user_id=provider_user_id,
        )
        self._session.add(new_identity)
        await self._session.refresh()
        return new_identity

    async def delete_auth_identity(self, user_id: UUID) -> bool:
        stmt = delete(AuthIdentity).where(AuthIdentity.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def count_auth_identities(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(AuthIdentity)
            .where(AuthIdentity.user_id == user_id)
        )

        return self._session.scalar(stmt) or 0

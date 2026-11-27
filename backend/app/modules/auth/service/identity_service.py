from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.auth.dto.auth_identity import AuthIdentityDTO
from backend.app.modules.auth.dto.resolved_identity import ResolvedIdentityDTO
from backend.app.modules.auth.dto.user_identity import UserIdentityDTO
from backend.app.modules.auth.exceptions import (
    IdentityAlreadyLinkedError,
    IdentityDeleteError,
    LastIdentityError,
)
from backend.app.modules.auth.models.auth_identity import AuthProvider
from backend.app.modules.auth.repository.auth_identity import AuthIdentityRepo
from backend.app.modules.user.dto.user import UserDTO
from backend.app.modules.user.service.user_service import UserService


class IdentityService:
    def __init__(self, session: AsyncSession):
        self._auth_repo = AuthIdentityRepo(session=session)
        self._user_service = UserService(session=session)

    async def resolve(
        self,
        identity: UserIdentityDTO,
    ) -> ResolvedIdentityDTO:
        """
        Находит внешнюю идентичность.

        Если она существует:
            возвращает пользователя и идентичность.

        Если отсутствует:
            создаёт пользователя,
            создаёт внешнюю идентичность,
            возвращает оба объекта.
        """
        user_identity = await self._auth_repo.get_auth_identity_by_user_id(
            auth_provider=identity.provider, provider_user_id=identity.external_id
        )
        if user_identity:
            return ResolvedIdentityDTO(
                user=UserDTO(
                    id=user_identity.user.id,
                    name=user_identity.user.name,
                    is_active=user_identity.user.is_active,
                ),
                identity=AuthIdentityDTO(
                    id=user_identity.id,
                    user_id=user_identity.user.id,
                    provider_user_id=user_identity.provider_user_id,
                    auth_provider=identity.provider,
                ),
            )

        new_user = await self._user_service.create_user(name=identity.first_name)
        new_identity = await self._auth_repo.create_auth_identity(
            user_id=new_user.id,
            auth_provider=identity.provider,
            provider_user_id=identity.external_id,
        )

        if new_identity.user_id != new_user.id:
            await self._user_service.delete_user(user_id=new_user.id)
            existing_user = await self._user_service.get_active_user(
                user_id=new_identity.user_id
            )
            return ResolvedIdentityDTO(
                user=existing_user,
                identity=AuthIdentityDTO(
                    id=new_identity.id,
                    user_id=new_identity.user_id,
                    auth_provider=new_identity.auth_provider,
                    provider_user_id=new_identity.provider_user_id,
                ),
            )

        return ResolvedIdentityDTO(
            user=new_user,
            identity=AuthIdentityDTO(
                id=new_identity.id,
                user_id=new_user.id,
                auth_provider=new_identity.auth_provider,
                provider_user_id=new_identity.provider_user_id,
            ),
        )

    async def link_identity(
        self,
        user_id: UUID,
        identity: UserIdentityDTO,
    ) -> AuthIdentityDTO:
        """
        Привязывает новую внешнюю идентичность
        к существующему пользователю.
        """
        auth_identity = await self._auth_repo.get_auth_identity_by_user_id(
            auth_provider=identity.provider,
            provider_user_id=identity.external_id,
        )
        if auth_identity is not None:
            if auth_identity.user_id != user_id:
                raise IdentityAlreadyLinkedError()
            return AuthIdentityDTO(
                id=auth_identity.id,
                user_id=auth_identity.user_id,
                auth_provider=auth_identity.auth_provider,
                provider_user_id=auth_identity.provider_user_id,
            )

        new_auth_identity = await self._auth_repo.create_auth_identity(
            user_id=user_id,
            auth_provider=identity.provider,
            provider_user_id=identity.external_id,
        )
        return AuthIdentityDTO(
            id=new_auth_identity.id,
            user_id=new_auth_identity.user_id,
            auth_provider=new_auth_identity.auth_provider,
            provider_user_id=new_auth_identity.provider_user_id,
        )

    async def unlink_identity(
        self, user_id: UUID, provider: AuthProvider, provider_user_id: str
    ) -> None:
        """
        Отвязывает внешнюю идентичность.
        Не позволяет удалить последний способ входа.
        """
        count_auth = await self._auth_repo.count_auth_identities(user_id=user_id)
        if count_auth <= 1:
            raise LastIdentityError()

        if not await self._auth_repo.delete_auth_identity(
            user_id=user_id,
            auth_provider=provider,
            provider_user_id=provider_user_id,
        ):
            raise IdentityDeleteError(message="Не удалось удалить идентичность")

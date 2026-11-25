from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.user.dto.user import UserDTO
from backend.app.modules.user.repository.user_repo import UserRepository


class UserService:
    def __init__(self, session: AsyncSession):
        self._user_repo = UserRepository(session=session)

    async def create_user(self, name: str) -> UserDTO:
        user = await self._user_repo.create_user(name=name)
        return UserDTO(id=user.id, name=user.name, is_active=user.is_active)

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.session import get_async_session
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.service.user_service import UserService


def get_token_service() -> TokenService:
    return TokenService()


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserService:
    return UserService(session=session)

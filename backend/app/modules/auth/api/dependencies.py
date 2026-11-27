from typing import Annotated

from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.session import get_async_session
from backend.app.modules.auth.service.auth_service import AuthService
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.api.dependencies import (
    get_token_service,
    get_user_service,
)
from backend.app.modules.user.schemas.response import UserResponse
from backend.app.modules.user.service.user_service import UserService


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AuthService:
    return AuthService(session=session)


def get_refresh_token(refresh_token: str | None = Cookie(default=None)) -> str:
    if refresh_token is None:
        raise  # TODO Нужно будет выбросить ошибку что нету куки

    return refresh_token


def get_user_session_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> SessionService:
    return SessionService(session=session)


async def get_current_user(
    _token_service: Annotated[TokenService, Depends(get_token_service)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer)],
    _user_service: Annotated[UserService, Depends(get_user_service)],
    _user_session_service: Annotated[SessionService, Depends(get_user_session_service)],
):
    result = _token_service.decode_access_token(credentials.credentials)
    user_session = await _user_session_service.get_by_active_session(
        user_session_id=result.get("sid", None), user_id=result.get("sub", None)
    )

    user = await _user_service.get_active_user(user_id=user_session.user_id)

    return UserResponse(id=user.id, name=user.name, is_active=user.is_active)

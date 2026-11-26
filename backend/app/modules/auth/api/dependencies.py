from typing import Annotated

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.session import get_async_session
from backend.app.modules.auth.service.auth_service import AuthService
from backend.app.modules.auth.service.session_service import SessionService


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

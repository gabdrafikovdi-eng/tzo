from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from backend.app.core.config import Settings, get_settings
from backend.app.modules.auth.api.dependencies import (
    get_auth_service,
    get_current_user,
    get_refresh_token,
)
from backend.app.modules.auth.schemas.request import TelegramAuthRequest
from backend.app.modules.auth.schemas.response import AuthResponse
from backend.app.modules.auth.service.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post(
    "/telegram", response_model=AuthResponse, status_code=status.HTTP_200_OK
)
async def authenticate_telegram(
    data: TelegramAuthRequest,
    response: Response,
    _auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    result = await _auth_service.authenticate_telegram(init_data=data.init_data)
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=settings.HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return AuthResponse(access_token=result.access_token, token_type="Bearer")


@auth_router.post(
    "/refresh", response_model=AuthResponse, status_code=status.HTTP_200_OK
)
async def refresh_tokens(
    response: Response,
    refresh_token: Annotated[str, Depends(get_refresh_token)],
    _auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    result = await _auth_service.refresh_tokens(refresh_token=refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=result.refresh_token,
        httponly=settings.HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return AuthResponse(access_token=result.access_token, token_type="Bearer")


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Annotated[str, Depends(get_refresh_token)],
    _auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        secure=settings.COOKIE_SECURE,
        httponly=settings.HTTPONLY,
        samesite="lax",
    )
    await _auth_service.logout(refresh_token=refresh_token)


@auth_router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    current_user: Annotated[dict, Depends(get_current_user)],
    _auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        secure=settings.COOKIE_SECURE,
        httponly=settings.HTTPONLY,
        samesite="lax",
    )
    await _auth_service.all_logout(user_id=current_user.id)

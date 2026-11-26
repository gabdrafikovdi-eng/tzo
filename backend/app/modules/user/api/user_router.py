from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.modules.auth.api.dependencies import get_user_session_service
from backend.app.modules.auth.service.session_service import SessionService
from backend.app.modules.auth.service.token_service import TokenService
from backend.app.modules.user.api.dependencies import (
    get_token_service,
    get_user_service,
)
from backend.app.modules.user.schemas.response import UserResponse
from backend.app.modules.user.service.user_service import UserService

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.get(
    path="/me", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def get_me(
    access_token: str,
    _token_service: Annotated[TokenService, Depends(get_token_service)],
    _user_service: Annotated[UserService, Depends(get_user_service)],
    _user_session_service: Annotated[SessionService, Depends(get_user_session_service)],
) -> UserResponse:
    result = _token_service.decode_access_token(token=access_token)
    user_session = await _user_session_service.get_by_active_session(
        user_session_id=result.get("sid", None), user_id=result.get("sub", None)
    )

    user = await _user_service.get_active_user(user_id=user_session.user_id)

    return UserResponse(id=user.id, name=user.name, is_active=user.is_active)

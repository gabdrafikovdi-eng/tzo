from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.app.modules.auth.api.dependencies import get_current_user
from backend.app.modules.user.schemas.response import UserResponse

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.get(
    path="/me", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def get_me(
    user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    return user

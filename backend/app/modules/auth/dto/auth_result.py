from dataclasses import dataclass
from datetime import datetime

from backend.app.modules.user.dto.user import UserDTO


@dataclass(frozen=True, slots=True)
class AuthResultDTO:
    user: UserDTO
    access_token: str
    refresh_token: str
    refresh_expires_at: datetime

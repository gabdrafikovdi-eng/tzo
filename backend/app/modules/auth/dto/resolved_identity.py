from dataclasses import dataclass

from backend.app.modules.auth.dto.auth_identity import AuthIdentityDTO
from backend.app.modules.user.dto.user import UserDTO


@dataclass
class ResolvedIdentityDTO:
    user: UserDTO
    identity: AuthIdentityDTO

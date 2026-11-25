from dataclasses import dataclass
from uuid import UUID

from backend.app.modules.auth.models.auth_identity import AuthProvider


@dataclass(frozen=True, slots=True)
class AuthIdentityDTO:
    id: UUID
    user_id: UUID
    auth_provider: AuthProvider
    provider_user_id: str

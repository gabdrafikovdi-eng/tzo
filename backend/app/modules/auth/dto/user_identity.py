from dataclasses import dataclass

from backend.app.modules.auth.models.auth_identity import AuthProvider


@dataclass(frozen=True, slots=True)
class UserIdentityDTO:
    provider: AuthProvider
    external_id: str
    email: str | None = None
    email_verified: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    locale: str | None = None

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserSessionDTO:
    id: UUID
    user_id: UUID
    refresh_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None

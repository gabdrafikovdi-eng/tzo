from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TokenPairDTO:
    refresh_token: str
    access_token: str
    refresh_expires_at: datetime

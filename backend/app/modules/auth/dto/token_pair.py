from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TokenPairDTO:
    refresh_token: str
    access_token: str

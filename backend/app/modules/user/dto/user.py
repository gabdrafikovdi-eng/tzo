from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    name: str | None
    is_active: bool

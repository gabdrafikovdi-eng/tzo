from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.core.base import Base, TimestampMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.modules.auth.models.auth_identity import AuthIdentity


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(30), default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    auth_identities: Mapped[list["AuthIdentity"]] = relationship(
        "AuthIdentity", back_populates="user"
    )

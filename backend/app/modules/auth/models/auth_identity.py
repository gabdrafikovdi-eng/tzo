from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.core.base import Base, TimestampMixin
from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from backend.app.modules.user.models.user import User


class AuthProvider(StrEnum):
    TELEGRAM = "telegram"


class AuthIdentity(Base, TimestampMixin):
    __tablename__ = "auth_identities"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        default=uuid4,
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    auth_provider: Mapped[AuthProvider] = mapped_column(
        Enum(
            AuthProvider,
            name="auth_provider",
            native_enum=False,
            values_callable=lambda enum: [x.value for x in enum],
        ),
        nullable=False,
    )

    provider_user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="auth_identities",
    )

    __table_args__ = (
        UniqueConstraint(
            "auth_provider",
            "provider_user_id",
            name="uq_auth_identity_provider_user",
        ),
    )

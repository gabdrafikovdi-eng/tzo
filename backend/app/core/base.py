import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_mixin, mapped_column


class Base(DeclarativeBase):
    pass


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(  # type: ignore
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

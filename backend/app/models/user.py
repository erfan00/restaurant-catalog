from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Null for users created purely via an external OAuth provider (no local
    # password). Present for OAuth2-password-flow demo users.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Set when the account originates from an external OAuth provider, e.g.
    # "google". Null for local password accounts.
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    restaurants: Mapped[list[Restaurant]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"User(id={self.id!r}, email={self.email!r})"

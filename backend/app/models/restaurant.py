from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.user import User


class Restaurant(TimestampMixin, Base):
    __tablename__ = "restaurants"
    __table_args__ = (UniqueConstraint("name", name="uq_restaurants_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner: Mapped[User] = relationship(back_populates="restaurants")

    menu_items: Mapped[list[MenuItem]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan", order_by="MenuItem.id"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Restaurant(id={self.id!r}, name={self.name!r})"

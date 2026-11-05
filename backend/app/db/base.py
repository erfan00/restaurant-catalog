"""Declarative base for all ORM models."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base. Import models that subclass this so Alembic
    autogenerate and `Base.metadata.create_all` can discover them."""

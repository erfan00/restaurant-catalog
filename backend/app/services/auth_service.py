"""Business logic for user registration and authentication."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise EmailAlreadyRegisteredError(payload.email)

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None or user.hashed_password is None:
        raise InvalidCredentialsError(email)
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError(email)
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id))


async def get_or_create_oauth_user(
    db: AsyncSession, *, email: str, full_name: str | None, provider: str
) -> User:
    """Used by the real-OAuth (Google) callback to find-or-create a local
    user record for a federated identity. No password is set."""
    user = await get_user_by_email(db, email)
    if user is not None:
        return user
    user = User(email=email, full_name=full_name, oauth_provider=provider)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

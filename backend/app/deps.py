"""Shared FastAPI dependencies: DB session + current user resolution."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenError, subject_from_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer JWT.

    Raises 401 if there is no token, the token is invalid/expired, or the
    user it refers to no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    try:
        user_id = subject_from_token(token)
    except TokenError as exc:
        raise credentials_exception from exc

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising, for
    endpoints that are public but behave differently when authenticated."""
    if token is None:
        return None
    try:
        user_id = subject_from_token(token)
    except TokenError:
        return None
    return await get_user_by_id(db, int(user_id))

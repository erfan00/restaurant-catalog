"""Authentication endpoints.

Primary demo flow: OAuth2 "password" grant (RFC 6749 section 4.3) issuing a
JWT access token, implemented with FastAPI's OAuth2PasswordRequestForm and
OAuth2PasswordBearer. This is a real, spec-compliant OAuth2 flow that does
not require a third-party provider or network access, which makes it
reliable in CI / sandboxes.

A stubbed Google OAuth2 "authorization code" flow is also included
(disabled unless GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI
are set) to document exactly how to swap in real Google/GitHub login — see
README "Auth flow" for details.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    authenticate_user,
    issue_token_for_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await register_user(db, payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{exc}' is already registered",
        ) from exc


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return Token(access_token=issue_token_for_user(user))


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/google/login")
async def google_login() -> dict[str, str]:
    """Would redirect to Google's consent screen in a real deployment.

    Disabled in this sandbox because it requires real Google OAuth
    credentials and outbound network access. See README for the handful of
    lines (using authlib's `OAuth` client) needed to make this a genuine
    redirect once GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI are configured.
    """
    if not settings.google_oauth_configured:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, "
                "GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI, or use "
                "POST /auth/register and /auth/token instead."
            ),
        )
    # Real implementation (requires `authlib`, see README):
    #   return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)
    raise HTTPException(  # pragma: no cover - unreachable without real creds
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth client not wired up in this environment.",
    )


@router.get("/google/callback")
async def google_callback() -> dict[str, str]:  # pragma: no cover - documentation stub
    """Callback target for the Google OAuth2 authorization code flow.

    See README for the real implementation outline (exchange `code` for
    tokens via `oauth.google.authorize_access_token`, fetch the user's
    profile, then call `get_or_create_oauth_user` and issue our own JWT via
    `issue_token_for_user` so the rest of the API doesn't need to know which
    login method was used).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google OAuth client not wired up in this environment.",
    )

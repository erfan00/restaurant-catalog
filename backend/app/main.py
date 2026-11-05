"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.routers import auth, menu_items, restaurants

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # For local SQLite dev, create tables automatically on startup so the
    # app "just works" without running Alembic first. In production
    # (Postgres), schema is managed by Alembic migrations instead - see
    # README "Database migrations".
    if settings.database_url.startswith("sqlite") and settings.environment != "test":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "A restaurant & menu catalog API: public browsing, owner-only "
        "editing, OAuth2 (password/JWT) login with a documented path to "
        "real Google/GitHub OAuth."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(menu_items.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

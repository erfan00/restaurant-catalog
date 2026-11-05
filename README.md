# Restaurant Catalog

A restaurant & menu catalog web app: browse restaurants and their menus
publicly, log in, and manage (create/edit/delete) the restaurants you own
and their menu items.

This is a 2026 rebuild of a university project originally built in 2016 with
Flask + OAuth2 + AWS. The domain is unchanged (restaurants, menus, owner
login); the stack and practices are not: FastAPI + SQLAlchemy 2.0 (async) on
the backend, a typed React SPA on the frontend, real tests, CI, and
containerized local deploy.

## Table of contents

- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project layout](#project-layout)
- [Quick start (Docker Compose)](#quick-start-docker-compose)
- [Manual local setup](#manual-local-setup)
- [Demo walkthrough](#demo-walkthrough)
- [Auth flow](#auth-flow)
- [API reference](#api-reference)
- [Database & migrations](#database--migrations)
- [Testing & code quality](#testing--code-quality)
- [CI](#ci)
- [Limitations / what's intentionally out of scope](#limitations--whats-intentionally-out-of-scope)

## Architecture

```
                         ┌──────────────────────────┐
                         │        Browser SPA        │
                         │  React + TypeScript (Vite)│
                         └─────────────┬─────────────┘
                                       │  fetch() / JSON
                                       │  Authorization: Bearer <JWT>
                                       ▼
                         ┌──────────────────────────┐
                         │        FastAPI app         │
                         │ ┌───────────────────────┐ │
                         │ │ routers (HTTP layer)   │ │   /auth, /restaurants,
                         │ │  auth / restaurants /  │ │   /restaurants/{id}/menu-items
                         │ │  menu_items            │ │
                         │ └───────────┬────────────┘ │
                         │ ┌───────────▼────────────┐ │
                         │ │ services (business logic)│
                         │ │  auth / restaurant /     │ │
                         │ │  menu_item               │ │
                         │ └───────────┬────────────┘ │
                         │ ┌───────────▼────────────┐ │
                         │ │ models (SQLAlchemy 2.0) │ │
                         │ │  User / Restaurant /     │ │
                         │ │  MenuItem                │ │
                         │ └───────────┬────────────┘ │
                         └─────────────┼──────────────┘
                                       │ async engine
                                       ▼
                         ┌──────────────────────────┐
                         │   SQLite (dev) /           │
                         │   PostgreSQL (prod)        │
                         └──────────────────────────┘
```

Request flow for a write (e.g. "edit restaurant"):

1. SPA sends `PUT /restaurants/{id}` with `Authorization: Bearer <jwt>`.
2. `app/deps.py::get_current_user` decodes the JWT and loads the `User`.
3. `app/routers/restaurants.py::get_owned_restaurant` loads the restaurant
   and checks `restaurant.owner_id == current_user.id`, else `403`.
4. `app/services/restaurant_service.py` applies the update and commits.
5. Response is serialized through a pydantic v2 schema back to the SPA.

## Tech stack

**Backend**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0, fully async (`asyncio` + `aiosqlite` / `asyncpg`)
- Alembic migrations
- Pydantic v2 schemas
- OAuth2 "password" grant + JWT (see [Auth flow](#auth-flow))
- pytest + FastAPI `TestClient` for unit + API integration tests
- ruff, black, mypy

**Frontend**
- React 18 + TypeScript, built with Vite
- Plain fetch-based API client (no heavy data-fetching library needed at
  this scale) with a small typed wrapper in `src/api.ts`
- Hand-written CSS (no component library - deliberately lightweight)
- eslint (flat config) + prettier

**Infra**
- Docker Compose (backend + nginx-served frontend build)
- GitHub Actions CI (backend lint/type-check/tests, frontend lint/build)

## Project layout

```
restaurant-catalog/
├── backend/
│   ├── app/
│   │   ├── core/        # settings (config.py), security (JWT/password hashing)
│   │   ├── db/          # declarative Base + async session/engine
│   │   ├── models/      # SQLAlchemy ORM models: User, Restaurant, MenuItem
│   │   ├── schemas/     # pydantic v2 request/response models
│   │   ├── services/    # business logic / DB access, framework-agnostic
│   │   ├── routers/     # FastAPI routers (HTTP layer only)
│   │   ├── deps.py       # shared dependencies (current user, etc.)
│   │   └── main.py       # app factory / startup
│   ├── alembic/          # migrations (one initial migration included)
│   ├── tests/            # pytest unit + API integration tests
│   ├── requirements.txt / requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api.ts              # typed fetch client
│   │   ├── types.ts            # shared TS types mirroring pydantic schemas
│   │   ├── AuthContext.tsx     # auth state provider
│   │   ├── useAuth.ts          # auth hook
│   │   ├── App.tsx             # top-level layout/routing (single page)
│   │   └── components/         # LoginPanel, RestaurantList/Detail, forms
│   └── Dockerfile / nginx.conf
├── .github/workflows/ci.yml
├── docker-compose.yml
├── LICENSE (MIT)
└── README.md
```

## Quick start (Docker Compose)

Requires Docker + Docker Compose.

```bash
cd restaurant-catalog
docker compose up --build
```

- Backend: http://localhost:8000 (docs at http://localhost:8000/docs)
- Frontend: http://localhost:5173

This uses SQLite inside the backend container by default (zero config). To
use Postgres instead, uncomment the `postgres` service and the
`DATABASE_URL` override in `docker-compose.yml` (see inline comments there).

> Note: the Docker Compose setup was authored and reviewed carefully but
> could not be executed inside this sandbox (no Docker daemon available
> here). Both Dockerfiles use standard, well-tested patterns (python:3.12-slim
> + pip install; node:20-alpine build -> nginx:1.27-alpine serve) and the
> underlying commands (`pip install -r requirements.txt`, `npm install &&
> npm run build`) were verified directly on the host - see
> [Testing & code quality](#testing--code-quality) for exactly what was run.

## Manual local setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env              # optional, defaults already work
uvicorn app.main:app --reload --port 8000
```

The app auto-creates its SQLite tables on startup in dev (see
`app/main.py`'s `lifespan`). Visit http://localhost:8000/docs for interactive
OpenAPI docs (Swagger UI) - every endpoint, request/response schema, and
auth requirement is documented there automatically.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173. The Vite dev server proxies `/api/*` to
`http://localhost:8000` (see `vite.config.ts`), so the backend must be
running first.

## Demo walkthrough

With both backend and frontend running (either via Docker Compose or
manually):

1. Open http://localhost:5173 (or :5173 if using the manual frontend). You
   see "Restaurants" with an empty list and a "Browsing as a guest" badge.
2. Click **Register** in the login panel, enter any email and an 8+
   character password, submit. You're now logged in (JWT stored in
   `localStorage`) and see "Signed in as ...".
3. Click **+ New** to create a restaurant (name required; cuisine,
   description, address optional). Submit - it appears in the sidebar and
   is auto-selected.
4. On the restaurant detail panel, click **+ Add menu item**, fill in name
   + price, submit. It shows up under "Menu".
5. Click **Edit** on the restaurant or a menu item to change it in place,
   or **Delete** to remove it (confirmation prompt first).
6. Log out. The restaurant and its menu are still publicly visible (read is
   public), but the **Edit/Delete** buttons disappear - you're no longer
   the owner in this session.
7. Register a second account and try to hit
   `PUT /restaurants/{id}` for the first user's restaurant directly (e.g.
   via `curl` or the OpenAPI docs "Try it out") - the API returns `403
   Forbidden`. Omit the `Authorization` header entirely and it returns `401
   Unauthorized`. This 401-vs-403 distinction is deliberate and covered by
   `backend/tests/test_authorization.py`.

## Auth flow

**What's implemented and running:** a real, spec-compliant OAuth2
["password" grant](https://datatracker.ietf.org/doc/html/rfc6749#section-4.3)
(`POST /auth/token`, built on FastAPI's `OAuth2PasswordRequestForm` and
`OAuth2PasswordBearer`), issuing a signed JWT access token. Passwords are
hashed with bcrypt. This flow requires no outbound network access or
third-party credentials, which is why it's the default here - it's genuinely
OAuth2 (not a bespoke scheme), just using the first-party "password" grant
type instead of a third-party "authorization code" grant.

```
POST /auth/register  {email, password}        -> 201 User
POST /auth/token      (form) username,password -> 200 {access_token, token_type}
GET  /auth/me         Authorization: Bearer ...-> 200 User
```

**Why not wire up real Google/GitHub OAuth here:** the "authorization code"
flow those use requires a registered OAuth app with real client
credentials and a reachable redirect URI, plus outbound HTTPS calls to the
provider during the callback - none of which is available or reliable in
this sandboxed build/CI environment. Rather than fake it, the code documents
exactly how to swap it in:

- `app/core/config.py` already has `google_client_id` /
  `google_client_secret` / `google_redirect_uri` settings, defaulting to
  unset (`google_oauth_configured` is `False`).
- `app/routers/auth.py` has `GET /auth/google/login` and
  `GET /auth/google/callback` stubs that return `501 Not Implemented` while
  unconfigured, with comments showing the ~10 lines needed for a real
  implementation using [`authlib`](https://docs.authlib.org/) (already a
  listed dependency):

  ```python
  from authlib.integrations.starlette_client import OAuth
  oauth = OAuth()
  oauth.register(
      name="google",
      server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
      client_id=settings.google_client_id,
      client_secret=settings.google_client_secret,
      client_kwargs={"scope": "openid email profile"},
  )

  @router.get("/google/login")
  async def google_login(request: Request):
      return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)

  @router.get("/google/callback")
  async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
      token = await oauth.google.authorize_access_token(request)
      profile = token["userinfo"]
      user = await get_or_create_oauth_user(
          db, email=profile["email"], full_name=profile.get("name"), provider="google"
      )
      return Token(access_token=issue_token_for_user(user))
  ```

- `app/services/auth_service.py::get_or_create_oauth_user` and
  `issue_token_for_user` already exist specifically to support this - the
  rest of the API (restaurant/menu-item ownership checks, `get_current_user`)
  is identical regardless of how the user authenticated, because both paths
  converge on the same JWT-issuing step.

**Authorization (ownership enforcement):** every restaurant has an
`owner_id`. Public `GET` endpoints never check auth. Every `POST` to
`/restaurants` attaches the current user as owner. Every `PUT`/`DELETE` on a
restaurant or its menu items goes through `get_owned_restaurant` (in
`app/routers/restaurants.py`), which:

- Returns `401` if there's no valid bearer token at all.
- Returns `404` if the restaurant doesn't exist.
- Returns `403` if the caller is authenticated but isn't the owner.

This is enforced entirely server-side (the frontend hiding Edit/Delete
buttons is a UX nicety, not the security boundary) and is covered by
`backend/tests/test_authorization.py` and the ownership tests in
`test_restaurants.py` / `test_menu_items.py`.

## API reference

Full interactive reference: run the backend and visit **`/docs`**
(Swagger UI) or **`/redoc`**. It's generated from the pydantic schemas and
is always in sync with the code. Summary:

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | none | Create a local account |
| POST | `/auth/token` | none | OAuth2 password grant -> JWT |
| GET | `/auth/me` | required | Current user |
| GET | `/auth/google/login` | none | 501 unless Google OAuth configured |
| GET | `/restaurants` | none | List restaurants |
| POST | `/restaurants` | required | Create restaurant (caller becomes owner) |
| GET | `/restaurants/{id}` | none | Restaurant detail + menu items |
| PUT | `/restaurants/{id}` | owner | Update restaurant |
| DELETE | `/restaurants/{id}` | owner | Delete restaurant (cascades menu items) |
| GET | `/restaurants/{id}/menu-items` | none | List menu items |
| POST | `/restaurants/{id}/menu-items` | owner | Create menu item |
| GET | `/restaurants/{id}/menu-items/{item_id}` | none | Menu item detail |
| PUT | `/restaurants/{id}/menu-items/{item_id}` | owner | Update menu item |
| DELETE | `/restaurants/{id}/menu-items/{item_id}` | owner | Delete menu item |
| GET | `/health` | none | Liveness probe |

Error semantics used consistently: `401` (no/invalid token), `403`
(authenticated, not the owner), `404` (resource missing), `409` (duplicate
name), `422` (validation, e.g. missing/invalid fields).

## Database & migrations

- **Local dev default:** SQLite via `aiosqlite`, file `restaurant_catalog.db`
  in `backend/`. Tables are auto-created on startup for convenience.
- **Production:** set `DATABASE_URL` to an async Postgres DSN, e.g.:

  ```
  DATABASE_URL=postgresql+asyncpg://user:password@host:5432/restaurant_catalog
  ```

  and manage schema with Alembic instead of relying on startup
  auto-create:

  ```bash
  cd backend
  alembic upgrade head
  ```

  The included migration (`alembic/versions/0001_initial_schema.py`) creates
  `users`, `restaurants`, and `menu_items` with the same constraints as the
  ORM models (unique restaurant names, unique menu item name per restaurant,
  `ON DELETE CASCADE` from restaurant -> menu items).

## Testing & code quality

Everything below was **actually executed** in this environment (not just
code-reviewed) while building this project:

```bash
cd backend
source .venv/bin/activate
ruff check app tests        # -> All checks passed!
black --check app tests     # -> would be left unchanged
mypy app                    # -> Success: no issues found in 27 source files
pytest -v                   # -> 45 passed
```

The 45 backend tests cover: registration/login success + failure paths,
missing/invalid fields (422), duplicate email/restaurant/menu-item (409),
not-found (404), public read access without auth, create/update/delete
requiring auth (401 without a token), and ownership enforcement (403 for a
different authenticated user) - including explicit "401 vs 403" and
"malformed/expired/forged token" edge cases in `test_authorization.py`.

```bash
cd frontend
npm install
npm run lint          # -> eslint, 0 errors/warnings
npm run format:check  # -> prettier, all files formatted
npm run build         # -> tsc --noEmit (0 type errors) && vite build succeeds
```

The full stack was also exercised live end-to-end: backend started with
`uvicorn`, hit directly with `curl` (register -> login -> create restaurant
-> create menu item -> public list/detail -> unauthorized delete -> 401 ->
forbidden delete by a second user -> 403), then the same sequence repeated
through the Vite dev server's `/api` proxy (port 5173) to confirm the exact
path the browser SPA uses works end-to-end.

**Not executed in this environment:** `docker compose up` itself (no Docker
daemon available here) - see the note in
[Quick start](#quick-start-docker-compose).

## CI

`.github/workflows/ci.yml` runs on every push/PR with two independent jobs:

- **backend**: `ruff check`, `black --check`, `mypy`, `pytest -v`
- **frontend**: `eslint`, `prettier --check`, `npm run build` (which itself
  runs `tsc --noEmit` before `vite build`)

## Limitations / what's intentionally out of scope

- Real Google/GitHub OAuth is documented but not wired to live credentials
  (see [Auth flow](#auth-flow)) - there's nothing to configure safely in a
  public demo without real secrets, and the password/JWT flow demonstrates
  the same OAuth2 mechanics without that dependency.
- No pagination UI on the frontend (the API supports `skip`/`limit` query
  params on `GET /restaurants`; the SPA just requests the default page).
  Fine at demo scale; the next step for a larger catalog would be
  cursor/offset pagination controls in `RestaurantList`.
- No image uploads for restaurants/menu items (the 2016 original didn't
  meaningfully use S3 for this either) - would be a natural follow-up
  using signed URLs to S3-compatible storage.
- Single JWT secret from an env var, no refresh tokens / rotation - fine for
  a demo, a production system would want short-lived access tokens + refresh
  tokens.
- `docker compose up` was reviewed carefully (standard, minimal Dockerfiles)
  but not executed in this sandbox, which has no Docker daemon.

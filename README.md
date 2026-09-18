# FastAPI Template

A minimal, reusable starting point for a FastAPI backend: config, structured
logging, async Postgres via SQLAlchemy 2.0, Alembic migrations, JWT auth, and
one CRUD resource (`items`) that demonstrates the pattern to copy for your own
domain models.

No frontend yet, no tests/seed script/Dockerfile yet — see [What's not here](#whats-not-here-yet).

## What's included

- **Auth**: register, login (JWT), get current user. Passwords hashed with
  bcrypt via passlib; tokens signed with HS256 via python-jose.
- **One example resource** (`items`): owner-scoped CRUD with pagination —
  the pattern every future resource in your app should copy.
- **One error shape everywhere**: `{"error": {"code", "message", "details"}}`,
  via three global exception handlers in `main.py`.
- **Structured logging**, configured once, no `print()` anywhere.
- **All config in one place** — `app/core/config.py` — nothing reads
  `os.environ` directly and no constant is hardcoded at a call site.

## Structure

```
backend/
  app/
    main.py              # app factory: middleware, error handlers, router registration
    core/
      config.py           # pydantic-settings — every tunable lives here
      security.py         # password hashing, JWT create/decode (pure functions)
      logging.py          # one dictConfig call, run once at startup
    db/
      session.py          # async engine + per-request session dependency
      models.py            # SQLAlchemy models — User, Item
    schemas/              # Pydantic request/response models
    api/
      deps.py              # DbSession, CurrentUser — the two deps every route reuses
      routes/               # health.py, auth.py, items.py
    services/              # auth_service.py, item_service.py — plain functions, no HTTP concerns
  alembic/                # migrations — 0001_initial creates users + items
  tests/                  # empty — add your own (see below)
  .env.example
  requirements.txt         # runtime deps, exact-pinned
  requirements-dev.txt      # + pytest, httpx, ruff
docker-compose.yml          # Postgres for local dev
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows; source .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt

cp .env.example .env
# generate a real JWT_SECRET:
python -c "import secrets; print(secrets.token_urlsafe(32))"
# paste it into .env

docker compose up -d db           # starts Postgres on localhost:5433
alembic upgrade head              # creates users + items tables

uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs.

## How to add your own resource

Copy the `items` pattern — it's deliberately kept generic for exactly this:

1. Add a model to `app/db/models.py` (copy `Item`, rename, add your columns).
2. `alembic revision --autogenerate -m "add <thing>"`, review the generated
   migration, `alembic upgrade head`.
3. Add a schema file under `app/schemas/`.
4. Add a service file under `app/services/` — plain functions, filtered by
   `owner_id` if the resource belongs to a user.
5. Add a route file under `app/api/routes/`, register it in `main.py`.

Every route depends on `DbSession` and/or `CurrentUser` from `app/api/deps.py`
— that's the one pattern the whole app is built around.

## How to add your own config

Add a field to `Settings` in `app/core/config.py` and a matching line in
`.env.example`. That is the only place a tunable constant should ever live —
never inline at a call site.

## Design decisions worth knowing before you extend this

- **JWT in whatever the frontend chooses to store it in** — this template
  makes no frontend decision. If you store it in `localStorage`: any XSS
  on the page can read it, vs. an `httpOnly` cookie which JS can't read.
  The cookie route needs CSRF protection and same-site/cross-origin cookie
  config; `localStorage` + a short-lived token is the pragmatic default for
  a demo or an internal tool. For anything handling real user data, prefer
  an `httpOnly` refresh cookie + in-memory access token.
- **No roles, no refresh tokens, no repository pattern, no base
  classes.** Services are plain functions because each one has exactly one
  implementation — a repository/interface layer would be an abstraction with
  nothing to abstract over. Add roles or refresh tokens only when a real
  requirement needs them; both are self-contained additions, not
  foundational ones.
- **Owner-scoping returns 404, not 403**, for another user's row. Folding
  `owner_id` into the same query as the id lookup means "exists but isn't
  yours" is indistinguishable from "no such id" — a 403 would confirm the id
  exists at all. See `item_service.get_item`.
- **`passlib` is pinned with `bcrypt==4.0.1`, not the current bcrypt.**
  passlib 1.7.4 (last released 2020) probes its bcrypt backend in a way that
  bcrypt 5.x breaks — verified, not theoretical. See the comment in
  `requirements.txt`.

## What's not here yet

Left out of this template on purpose — add them in the specific app you build
from this, when that app actually needs them:

- **Frontend.** This is backend-only. Pair it with whatever your assignment
  specifies (React+Vite+TanStack Query is a solid default).
- **Tests, seed script, Dockerfile.** `tests/` exists but is empty — the
  pattern is `httpx.AsyncClient` + `ASGITransport` against a real test
  Postgres (`TEST_DATABASE_URL`), not against SQLite or mocks.
- **Rate limiting, request-ID correlation, CI.** Production hardening, not a
  starting point's job.

## Keeping this template current

Dependency versions in `requirements*.txt` were resolved and pinned from
PyPI on 2026-09-18, and every non-trivial API used was verified against the
real installed package, not assumed. Before reusing this months from now,
re-resolve the versions and re-run the smoke test below — a stale pin here
is a worse failure mode than an unpinned one, since it looks deliberate.

**Verifying after a version bump**, or just to confirm the template still
works:

```bash
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
# in another terminal:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersecret1"}'
curl -X POST http://localhost:8000/auth/login -d "username=you@example.com&password=supersecret1"
curl http://localhost:8000/auth/me -H "Authorization: Bearer <token from login>"
```

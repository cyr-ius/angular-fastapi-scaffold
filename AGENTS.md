# AGENTS.md

This file is the **single reference** for every AI agent (Claude, Copilot, Codex, Cursor...)
working in this repository. Change the rules here, not in agent-specific files.

The application is a FastAPI backend (`backend/`) serving an Angular frontend (`frontend/`),
shipped as one Docker image.

## A task is done only when

1. **The added or fixed behavior is covered by a relevant test**, existing or new
   (see [Tests](#tests)).
2. **The checks matching the modified files pass**, and only those
   (see [Checks by modified files](#checks-by-modified-files)).
3. **A schema change comes with its Alembic migration** (see [Database](#database)).
4. **`README.md` is up to date** when a setting, a command or a feature visible to the
   operator changed.
5. **The [security invariants](#security-invariants) still hold.**
6. **A security review of the changes was made with the `security-review` MCP server** when
   it is connected (see [Security review](#security-review)).

If one of these steps is deliberately skipped (e.g. an internal refactoring with no visible
effect), say so explicitly in the answer or in the pull request description, with the reason.
Never declare a task done without running the checks of the modified files.

### Checks by modified files

Run only the checks of the areas touched by the change (`git diff --stat`); CI runs everything
anyway.

| Modified files                     | Checks                                                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `backend/**`                       | `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` |
| `frontend/**`                      | `cd frontend && npm run build && npx ng test --watch=false`                                             |
| `Dockerfile`, `docker-compose.yml` | `docker compose up -d --build`, then `curl -f http://127.0.0.1:8000/api/health`                         |
| any file                           | `prek run --files <files>` (the pre-commit hooks, also run by CI)                                       |

## Agent behavior

Before making any change:

1. Read the relevant source files and follow their existing patterns.
2. Get the development standards of the technologies you touch from the MCP server (see
   [Coding conventions](#coding-conventions)) and apply them.
3. Make the smallest change that does the job.

Do not:

- add a dependency without a reason stated in the answer;
- replace a technology or a pattern of the project without approval;
- edit generated files (`uv.lock`, `package-lock.json`) by hand: use `uv` and `npm`;
- bypass a failing check (`--no-verify`, `# noqa` or `# type: ignore` without a reason);
- duplicate an existing component instead of extending it.

If a tool is missing or a command fails, report the command, the cause when known, and do
not hide the failure.

## Coding conventions

The development standards are provided by the `security-review` MCP server, and the
documentation of the frameworks (FastAPI, SQLModel, Angular...) by the `context7` MCP server;
both are declared in `.mcp.json`, and no skill is needed. Read the standards before writing
code:

- tool `get_development_standards`, by technology (`python`, `angular`...) or by file
  (`pyproject.toml`, `angular.json`...);
- tool `list_development_standards` to see the catalog;
- resource `standard://<slug>` to read one standard.

Do not copy them here. This file only keeps the rules specific to this repository; in case of
conflict, it wins. A standard never weakens security: keep the safe behavior and report the
conflict. If the server is not connected, say so, and follow the existing code.

## Technology stack

- **Backend**: Python 3.14, FastAPI, Pydantic 2, SQLModel (async SQLAlchemy, SQLite by
  default), Alembic, PyJWT, bcrypt; managed with `uv` (`pyproject.toml`, `uv.lock`).
- **Frontend**: Angular 22 (standalone components, signals, zoneless), Bootstrap 5,
  Vitest; Node.js 24, npm (`package-lock.json`).
- **Image**: multi-stage `Dockerfile` (Node build, `uv sync --locked`, Python runtime), runs
  as the unprivileged `app` user, data in the `/var/lib/app` volume.

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py           # application, lifespan (migrations, first admin), SPA serving
│   │   ├── config.py         # settings from the environment
│   │   ├── database.py       # async engine, sessions, migrate()
│   │   ├── models.py         # SQLModel tables
│   │   ├── security.py       # passwords, session tokens, security headers
│   │   ├── dependencies.py   # SessionDep, CurrentUser
│   │   ├── routers/          # one module per API area, all under /api
│   │   └── migrations/       # Alembic environment and revisions
│   └── tests/                # pytest, one file per area
├── frontend/src/app/
│   ├── core/                 # auth service, interceptor, guard, models
│   └── features/             # one folder per page (login, home...)
├── Dockerfile
├── docker-compose.yml
└── AGENTS.md
```

## Development

```bash
(cd backend && uv sync)                    # Python dependencies, dev group included
(cd frontend && npm ci)                    # Node dependencies from package-lock.json
prek install                               # pre-commit hooks

cd backend && DATA_DIR=../.data_env COOKIE_SECURE=false \
  uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm start                   # http://localhost:4200, /api proxied to :8000
```

The first start creates the `admin` account and logs its password once.
`COOKIE_SECURE=false` is for plain HTTP development only.

## Settings

Read from the environment (or `backend/.env`) by `app/config.py`: `APP_NAME`, `DATA_DIR`
(database and generated secret key, `/var/lib/app` in the image), `DATABASE_URL`,
`SECRET_KEY` (generated in `DATA_DIR` when empty), `ACCESS_TOKEN_EXPIRE_MINUTES`,
`COOKIE_SECURE`, `ADMIN_USERNAME`, `SWAGGER_ENABLED` (`/api/docs`), `LOG_LEVEL`.
`APP_VERSION` is set by the image from the release tag.

## Database

The application applies the migrations at startup (`migrate()` in the lifespan). After
changing `app/models.py`, generate and review the revision, then commit it:

```bash
cd backend && DATA_DIR=../.data_env uv run alembic revision --autogenerate -m "add item table"
```

## Tests

- Backend: pytest in `backend/tests/`, through `TestClient` (the lifespan runs, on a
  temporary `DATA_DIR`). Test the behavior through the HTTP API, including the refusals
  (401, 403, 404, validation errors), not only the nominal case.
- Frontend: Vitest specs next to the code (`*.spec.ts`), `HttpTestingController` for the
  HTTP calls.

## Security invariants

- The session token is a signed JWT (HS256, `exp` required) in an **HttpOnly,
  `SameSite=Strict`, `Secure` cookie** scoped to `/api`; it is never readable by
  JavaScript, never stored in `localStorage`, never in a URL.
- Every route under `/api` other than `/api/health` and `/api/auth/login` requires
  `CurrentUser` (or a stricter dependency).
- Login answers the same error, in the same time, for an unknown user and a wrong password.
- Passwords are only stored as bcrypt hashes; secrets never appear in logs (except the
  one-time initial admin password).
- The SPA route never serves a file outside `FRONTEND_DIR` (path traversal), and unknown
  `/api/*` paths answer 404, not `index.html`.
- `SecurityHeadersMiddleware` sends a strict Content-Security-Policy: no inline script (the
  frontend build does not inline critical CSS for that reason), no framing.
- The image runs as the unprivileged `app` user.

## Security review

When the `security-review` MCP server is connected (its prompts and tools appear in the
session), a security review of the changes is **systematic** before declaring a task done or
opening a pull request, whatever the size of the change:

1. Run the `security-review` prompt (or `api-security-review` for the API,
   `configuration-review` for the Dockerfile, workflows and YAML, `dependency-review` when
   `pyproject.toml`, `uv.lock` or `package.json` change) on the modified files, with the diff
   as context.
2. Use `scan_code` and `get_review_checklist` during the review.
3. Save the result **once** with `save_security_report` (`project`: the repository name, plus
   `branch` and `commit_sha` when known).
4. Fix the `critical` and `high` findings before finishing, with a test covering the fix. Fix
   or justify the others and propose their status with `propose_finding_status`: an agent never
   changes a status, a person validates the proposal in the web interface.
5. Summarize the review (report identifier, findings and what was done) in the answer and in
   the pull request description.

If the server is not connected or does not answer, say so explicitly: never claim a review
that was not made.

## Continuous integration and releases

The workflows call the reusable `web-` workflows of
[cyr-ius/.github](https://github.com/cyr-ius/.github): `ci.yml` (checks above),
`docker.yml` (build and smoke test of the image on every pull request), `codeql.yml`.

**After creating a project from this template:**

1. Rename the application: `name` in `docker-compose.yml`, `APP_NAME` default in
   `app/config.py`, `<title>` in `frontend/src/index.html`.
2. Create the `dev` branch and generate the release workflows (`publish.yml`, Release
   Please, docs) from a clone of cyr-ius/.github: `../dotgithub/web/sync.sh .`
3. Create the `DOCKERHUB_TOKEN` repository secret.

Development then happens on `dev`. Releases go through Release Please with Conventional
Commits (`feat:`, `fix:`...): merge `dev` into the default branch, then merge the release
pull request; the tag publishes the Docker image and the GitHub release. Do not push version
tags by hand.

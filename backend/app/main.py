"""Application entry point: API routers, then the Angular application."""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import select

from app.config import settings
from app.database import async_session, migrate
from app.models import User
from app.routers import auth, health
from app.security import SecurityHeadersMiddleware, hash_password

logging.basicConfig(
    level=settings.log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def create_admin() -> None:
    """Create the administrator on the first start, with a password shown once in the logs."""
    async with async_session() as session:
        if (await session.exec(select(User).limit(1))).first() is not None:
            return
        password = secrets.token_urlsafe(16)
        session.add(
            User(
                username=settings.admin_username,
                password_hash=hash_password(password),
                is_admin=True,
            )
        )
        await session.commit()
    logger.warning(
        "Administrator account created: username %r, password %r (shown only once)",
        settings.admin_username,
        password,
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await migrate()
    await create_admin()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.swagger_enabled else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if settings.swagger_enabled else None,
)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(health.router)
app.include_router(auth.router)


@app.get("/{path:path}", include_in_schema=False)
async def frontend(path: str) -> FileResponse:
    """Serve the Angular files; any other path gets index.html (client-side routing)."""
    if path == "api" or path.startswith("api/"):
        raise HTTPException(status_code=404)
    root = settings.frontend_dir.resolve()
    index = root / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404)
    candidate = (root / path).resolve()
    # resolve() follows "..": never serve a file outside the frontend directory
    if path and candidate.is_relative_to(root) and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(index)

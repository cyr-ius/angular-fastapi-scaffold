"""Each test session runs against its own temporary data directory."""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Before importing the application: its settings are read at import time
_DATA_DIR = Path(tempfile.mkdtemp(prefix="app-tests-"))
os.environ["DATA_DIR"] = str(_DATA_DIR)
os.environ["FRONTEND_DIR"] = str(_DATA_DIR / "frontend")
os.environ["COOKIE_SECURE"] = "false"  # the test client talks plain HTTP

from fastapi.testclient import TestClient  # noqa: E402

from app.database import async_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

PASSWORD = "correct horse battery staple"


@pytest.fixture(scope="session")
def frontend_dir() -> Path:
    root = _DATA_DIR / "frontend"
    root.mkdir(exist_ok=True)
    (root / "index.html").write_text("<app-root></app-root>")
    (root / "main.js").write_text("console.log('app')")
    # Outside the frontend directory: must never be served
    (_DATA_DIR / "secret.txt").write_text("secret")
    return root


@pytest.fixture(scope="session")
def client(frontend_dir: Path) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


async def _add_user(username: str, *, is_active: bool) -> None:
    async with async_session() as session:
        session.add(
            User(username=username, password_hash=hash_password(PASSWORD), is_active=is_active)
        )
        await session.commit()


@pytest.fixture(scope="session")
def user(client: TestClient) -> str:
    """Username of an active user whose password is PASSWORD."""
    client.portal.call(lambda: _add_user("alice", is_active=True))  # type: ignore[union-attr]
    return "alice"


@pytest.fixture(scope="session")
def disabled_user(client: TestClient) -> str:
    client.portal.call(lambda: _add_user("bob", is_active=False))  # type: ignore[union-attr]
    return "bob"


@pytest.fixture
def logged_in(client: TestClient, user: str) -> Iterator[TestClient]:
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert response.status_code == 200
    yield client
    client.cookies.clear()

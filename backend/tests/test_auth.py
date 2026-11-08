import jwt
from fastapi.testclient import TestClient

from app.config import settings
from tests.conftest import PASSWORD


def test_me_requires_a_session(client: TestClient) -> None:
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401


def test_login_sets_an_httponly_cookie(client: TestClient, user: str) -> None:
    response = client.post("/api/auth/login", json={"username": user, "password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"id": response.json()["id"], "username": user, "is_admin": False}
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert client.get("/api/auth/me").json()["username"] == user
    client.cookies.clear()


def test_wrong_password(client: TestClient, user: str) -> None:
    response = client.post("/api/auth/login", json={"username": user, "password": "wrong"})
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_unknown_user_gets_the_same_answer(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "nobody", "password": PASSWORD})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_disabled_user_cannot_log_in(client: TestClient, disabled_user: str) -> None:
    response = client.post(
        "/api/auth/login", json={"username": disabled_user, "password": PASSWORD}
    )
    assert response.status_code == 401


def test_logout_closes_the_session(logged_in: TestClient) -> None:
    assert logged_in.post("/api/auth/logout").status_code == 204
    assert logged_in.get("/api/auth/me").status_code == 401


def test_forged_token_is_rejected(client: TestClient) -> None:
    forged = jwt.encode({"sub": "1", "exp": 4102444800}, "not-the-secret-" * 4, algorithm="HS256")
    client.cookies.set(settings.session_cookie_name, forged, path="/api")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()


def test_unsigned_token_is_rejected(client: TestClient) -> None:
    unsigned = jwt.encode({"sub": "1", "exp": 4102444800}, None, algorithm="none")
    client.cookies.set(settings.session_cookie_name, unsigned, path="/api")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()


def test_expired_token_is_rejected(client: TestClient, user: str) -> None:
    expired = jwt.encode({"sub": "1", "exp": 1}, settings.secret_key, algorithm="HS256")
    client.cookies.set(settings.session_cookie_name, expired, path="/api")
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.clear()

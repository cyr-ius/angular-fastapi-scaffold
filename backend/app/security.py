"""Passwords, session tokens and HTTP security headers."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings

ALGORITHM = "HS256"
# Compared with when the user does not exist, so that the response time does not reveal it
_DUMMY_HASH = bcrypt.hashpw(b"dummy password", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    matches = bcrypt.checkpw(password.encode(), (password_hash or _DUMMY_HASH).encode())
    return matches and password_hash is not None


def create_session_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_session_token(token: str) -> int | None:
    """User id of a valid session token, None when it is invalid or expired."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.secret_key, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]}
        )
        return int(payload["sub"])
    except jwt.PyJWTError, ValueError:
        return None


SECURITY_HEADERS = {
    "content-security-policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "font-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    ),
    "referrer-policy": "strict-origin-when-cross-origin",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


class SecurityHeadersMiddleware:
    """Add the security headers to every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                present = {name.lower() for name, _ in headers}
                for name, value in SECURITY_HEADERS.items():
                    if name.encode() not in present:
                        headers.append((name.encode(), value.encode()))
            await send(message)

        await self.app(scope, receive, send_with_headers)

"""Database tables."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=150)
    password_hash: str
    is_admin: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)

"""Async database engine, sessions and schema migrations."""

from collections.abc import AsyncIterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _upgrade(connection: Connection) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")


async def migrate() -> None:
    """Bring the schema to the latest Alembic revision."""
    if settings.database_url.startswith("sqlite"):
        settings.data_dir.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as connection:
        await connection.run_sync(_upgrade)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session

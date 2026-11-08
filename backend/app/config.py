"""Settings, read from the environment (or a .env file)."""

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "App"
    # Set by the Docker image from the release tag
    app_version: str = "dev"
    log_level: str = "INFO"

    # Database, generated secret key and other persistent files
    data_dir: Path = Path("/var/lib/app")
    database_url: str = ""
    # Built Angular application served by the backend ("" or missing: API only)
    frontend_dir: Path = Path("/app/frontend")

    # Generated and kept in data_dir when empty
    secret_key: str = ""
    access_token_expire_minutes: int = 480
    session_cookie_name: str = "app_session"
    # Disable only to test over plain HTTP: browsers then send the cookie unencrypted
    cookie_secure: bool = True
    admin_username: str = "admin"
    # Interactive API documentation on /api/docs
    swagger_enabled: bool = False

    @model_validator(mode="after")
    def _defaults(self) -> Settings:
        if not self.database_url:
            self.database_url = f"sqlite+aiosqlite:///{self.data_dir}/database.db"
        if not self.secret_key:
            self.secret_key = _persistent_secret(self.data_dir / ".secret_key")
        return self


def _persistent_secret(path: Path) -> str:
    """Read the secret key of a previous start, or create it (readable by the owner only)."""
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_urlsafe(64)
    # O_EXCL: two workers starting together keep the key of the first one
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path.read_text().strip()
    with os.fdopen(fd, "w") as file:
        file.write(secret)
    logger.info("Secret key generated in %s", path)
    return secret


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

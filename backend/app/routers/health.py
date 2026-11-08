from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class Health(BaseModel):
    status: str
    app: str
    version: str


@router.get("/api/health")
async def health(request: Request) -> Health:
    """Liveness probe of the Docker HEALTHCHECK, without authentication."""
    return Health(status="healthy", app=request.app.title, version=request.app.version)

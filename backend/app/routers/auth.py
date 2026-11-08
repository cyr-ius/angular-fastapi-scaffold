from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import select

from app.config import settings
from app.dependencies import CurrentUser, SessionDep
from app.models import User
from app.security import create_session_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(max_length=150)
    password: str = Field(max_length=1024)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool


@router.post("/login")
async def login(body: LoginRequest, response: Response, session: SessionDep) -> UserRead:
    """Check the credentials and open the session in an HttpOnly cookie."""
    user = (await session.exec(select(User).where(User.username == body.username))).first()
    # Always check a hash, so that the response time does not reveal unknown users
    valid = verify_password(body.password, user.password_hash if user else None)
    if user is None or user.id is None or not valid or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    response.set_cookie(
        settings.session_cookie_name,
        create_session_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/api",
    )
    return UserRead.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/api",
    )


@router.get("/me")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)

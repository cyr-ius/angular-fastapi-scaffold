"""Shared route dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import User
from app.security import decode_session_token

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(request: Request, session: SessionDep) -> User:
    """User of the session cookie; 401 when it is missing, invalid or the user is disabled."""
    token = request.cookies.get(settings.session_cookie_name)
    user_id = decode_session_token(token) if token else None
    user = await session.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

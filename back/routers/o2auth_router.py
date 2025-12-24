from typing import Annotated
from datetime import datetime, timedelta, timezone
from typing import Annotated


from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..schemas import Token, TokenData
from ..models import User
from ..repo import get_user_repo
from ..utils import create_access_token, settings


o2auth_router = APIRouter(prefix="/auth", tags=["o2auth"])


@o2auth_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo=Depends(get_user_repo)
) -> Token:
    user: User | None = await user_repo.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_role": user.role}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
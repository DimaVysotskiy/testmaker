from fastapi import APIRouter, File, UploadFile
from typing import Annotated
from ..ai_utils import converter, testmaker
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

import dotenv
import os

from ..models import Token, TokenData, User, UserInDB
from ..repo import user_repo
from ..utils import authenticate_user, create_access_token, get_current_active_user, get_current_user, get_db



user_router = APIRouter(prefix="/user", tags=["user"])



@user_router.get("/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@user_router.get("/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
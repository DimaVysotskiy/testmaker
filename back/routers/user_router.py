from fastapi import APIRouter, File, UploadFile
from typing import Annotated
from typing import Annotated


from fastapi import Depends, FastAPI, HTTPException, status


from ..schemas import User
from ..repo import user_repo
from ..utils import get_current_active_user



user_router = APIRouter(prefix="/user", tags=["user"])



@user_router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@user_router.get("/me/items")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]
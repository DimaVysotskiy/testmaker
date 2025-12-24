from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
from .user_schemas import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str 
    user_role: UserRole

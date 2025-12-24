# back/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum




class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"




class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    password: str  


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  


class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None

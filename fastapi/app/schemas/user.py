from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.enums import RoleInSystem


class UserCreate(BaseModel):
    user_login: str = Field(..., min_length=3, max_length=255, description="Логин пользователя")
    password: str = Field(..., min_length=6, description="Пароль пользователя")
    user_role: RoleInSystem = Field(..., description="Роль пользователя (ADMIN, TEACHER, STUDENT)")


class UserResponse(BaseModel):
    id: int
    user_login: str
    user_role: RoleInSystem
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    user_login: str = Field(..., min_length=3, max_length=255, description="Логин пользователя")
    password: str = Field(..., min_length=6, description="Пароль пользователя")


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")
    user: UserResponse = Field(..., description="Данные пользователя")


from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union
from datetime import datetime
from app.models.enums import RoleInSystem


class UserCreate(BaseModel):
    user_login: str = Field(..., min_length=3, max_length=255, description="Логин пользователя")
    password: str = Field(..., min_length=6, description="Пароль пользователя")
    user_role: Union[RoleInSystem, int] = Field(..., description="Роль пользователя (ADMIN=1, TEACHER=2, STUDENT=3)")
    
    @field_validator('user_role', mode='before')
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            try:
                return RoleInSystem[v]
            except KeyError:
                raise ValueError(f"Неверная роль. Допустимые значения: {', '.join([r.name for r in RoleInSystem])}")
        elif isinstance(v, int):
            try:
                return RoleInSystem(v)
            except ValueError:
                raise ValueError(f"Неверное значение роли. Допустимые значения: {', '.join([str(r.value) for r in RoleInSystem])}")
        return v


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


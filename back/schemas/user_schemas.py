from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from ..enums import UserRole, OAuthProvider


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_email_verified: bool
    oauth_provider: OAuthProvider
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: Optional[str] = None
    oauth_id: Optional[str] = None
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
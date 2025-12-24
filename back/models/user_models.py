# back/models/user.py
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.sql import func
from ..utils import Base
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class OAuthProvider(str, enum.Enum):
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    LOCAL = "local"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255))
    
    hashed_password = Column(String(255))
    
    role = Column(
        SQLEnum(UserRole, name='user_role'),
        nullable=False,
        default=UserRole.STUDENT,
        index=True
    )
    
    oauth_provider = Column(
        SQLEnum(OAuthProvider, name='oauth_provider'),
        nullable=False,
        default=OAuthProvider.LOCAL,
        index=True
    )
    oauth_id = Column(String(255), index=True)
    oauth_access_token = Column(Text)
    oauth_refresh_token = Column(Text)
    oauth_token_expires_at = Column(DateTime)
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_email_verified = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    last_login_at = Column(DateTime)
    
    __table_args__ = (
        UniqueConstraint('oauth_provider', 'oauth_id', name='unique_oauth_provider_id'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
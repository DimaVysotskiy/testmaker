from sqlalchemy import Column, Integer, String, DateTime, func, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.models.enums import RoleInSystem

Base = declarative_base()


class User(Base):
    __tablename__ = "Users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_login = Column(String(255), unique=True, nullable=False, index=True)
    user_role = Column(Enum(RoleInSystem), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


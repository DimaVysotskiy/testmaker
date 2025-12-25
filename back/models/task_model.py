from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ARRAY, JSON,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from ..utils import Base
from ..enums import LessonType


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    files_metadata = Column(JSONB, nullable=True, default=[]) 
    photos_metadata = Column(JSONB, nullable=True, default=[])
    
    
    lesson_name = Column(String(255), nullable=False)
    lesson_type = Column(
        SQLEnum(LessonType, name='lesson_type'),
        nullable=False,
        index=True
    )
    
    checker = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    specialty = Column(String(255), nullable=False, index=True)
    course = Column(Integer, nullable=False, index=True)
    
    deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationship с пользователем
    checker_user = relationship("User", foreign_keys=[checker])
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, lesson_type={self.lesson_type})>"
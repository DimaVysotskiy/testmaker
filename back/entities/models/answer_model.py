from sqlalchemy import (
    Column, Integer, String, DateTime, Text,
    ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ...utils import Base
from ..enums import AnswerStatus


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    message = Column(Text, nullable=False)
    files_metadata = Column(JSONB, nullable=True, default=[])
    photos_metadata = Column(JSONB, nullable=True, default=[])
    
    status = Column(
        SQLEnum(AnswerStatus, name='answer_status'),
        nullable=False,
        default=AnswerStatus.SUBMITTED,
        index=True
    )
    grade = Column(Integer, CheckConstraint('grade >= 0 AND grade <= 100'), nullable=True)
    teacher_comment = Column(Text, nullable=True)
    
    add_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id])
    student = relationship("User", foreign_keys=[student_id])
    
    def __repr__(self):
        return f"<Answer(id={self.id}, task_id={self.task_id}, student_id={self.student_id}, status={self.status})>"

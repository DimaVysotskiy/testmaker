from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..enums import AnswerStatus


class FileMetadata(BaseModel):
    name: str
    url: str


class AnswerBase(BaseModel):
    task_id: int
    message: str
    files_metadata: List[FileMetadata] = Field(default_factory=list)
    photos_metadata: List[FileMetadata] = Field(default_factory=list)


class AnswerCreate(AnswerBase):
    """Схема для создания ответа студентом"""
    pass


class AnswerUpdate(BaseModel):
    """Схема для обновления ответа студентом (до проверки)"""
    message: Optional[str] = None
    files_metadata: Optional[List[FileMetadata]] = None
    photos_metadata: Optional[List[FileMetadata]] = None


class AnswerGrade(BaseModel):
    """Схема для выставления оценки преподавателем"""
    grade: int = Field(..., ge=0, le=100, description="Оценка от 0 до 100")
    teacher_comment: Optional[str] = None
    status: AnswerStatus = AnswerStatus.GRADED


class Answer(AnswerBase):
    """Схема для ответа"""
    id: int
    student_id: int
    status: AnswerStatus
    grade: Optional[int] = None
    teacher_comment: Optional[str] = None
    add_at: datetime
    graded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..enums import LessonType



class FileMetadata(BaseModel):
    name: str
    url: str



class TaskBase(BaseModel):
    title: str
    description: str
    lesson_name: str
    lesson_type: LessonType
    checker: int
    specialty: str
    course: int
    deadline: Optional[datetime] = None
    # Поля для файлов опциональны и по умолчанию пустые списки
    files_metadata: List[FileMetadata] = Field(default_factory=list)
    photos_metadata: List[FileMetadata] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Схема для создания задачи - все поля из TaskBase"""
    pass


class TaskUpdate(BaseModel):
    """Схема для обновления задачи - все поля опциональны"""
    title: Optional[str] = None
    description: Optional[str] = None
    files_metadata: Optional[List[str]] = None
    photos_metadata: Optional[List[str]] = None
    lesson_name: Optional[str] = None
    lesson_type: Optional[LessonType] = None
    checker: Optional[int] = None
    specialty: Optional[str] = None
    course: Optional[int] = None
    deadline: Optional[datetime] = None


class Task(TaskBase):
    """Схема для ответа - включает ID и все поля из TaskBase"""
    id: int
    
    class Config:
        from_attributes = True
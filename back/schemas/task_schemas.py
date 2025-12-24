from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..enums import LessonType


class TaskBase(BaseModel):
    title: str
    description: str
    file_urls: Optional[List[str]] = None
    photo_urls: Optional[List[str]] = None
    lesson_name: str
    lesson_type: LessonType
    checker: int
    specialty: str
    course: int
    deadline: datetime


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_urls: Optional[List[str]] = None
    photo_urls: Optional[List[str]] = None
    lesson_name: Optional[str] = None
    lesson_type: Optional[LessonType] = None
    checker: Optional[int] = None
    specialty: Optional[str] = None
    course: Optional[int] = None
    deadline: Optional[datetime] = None


class Task(TaskBase):
    id: int
    
    class Config:
        from_attributes = True
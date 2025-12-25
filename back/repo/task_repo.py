from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Sequence, Optional
from datetime import datetime

from ..repo import BaseRepository
from ..entities.models import Task
from ..utils import get_db
from ..entities.enums import LessonType


class TaskRepository(BaseRepository[Task]):
    """Репозиторий для работы с задачами"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_title(self, title: str) -> Task | None:
        """Получить задачу по названию"""
        statement = select(self.model).where(self.model.title == title)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_specialty_and_course(
        self, 
        specialty: str, 
        course: int
    ) -> Sequence[Task]:
        """Получить все задачи по специальности и курсу"""
        statement = select(self.model).where(
            self.model.specialty == specialty,
            self.model.course == course
        ).order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_lesson_type(
        self, 
        lesson_type: LessonType
    ) -> Sequence[Task]:
        """Получить все задачи по типу занятия"""
        statement = select(self.model).where(
            self.model.lesson_type == lesson_type
        ).order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_checker(self, checker_id: int) -> Sequence[Task]:
        """Получить все задачи проверяющего"""
        statement = select(self.model).where(
            self.model.checker == checker_id
        ).order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_upcoming_tasks(
        self, 
        specialty: str, 
        course: int
    ) -> Sequence[Task]:
        """Получить предстоящие задачи (дедлайн еще не прошел)"""
        statement = select(self.model).where(
            self.model.specialty == specialty,
            self.model.course == course,
            self.model.deadline > datetime.now()
        ).order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_overdue_tasks(
        self, 
        specialty: str, 
        course: int
    ) -> Sequence[Task]:
        """Получить просроченные задачи"""
        statement = select(self.model).where(
            self.model.specialty == specialty,
            self.model.course == course,
            self.model.deadline < datetime.now()
        ).order_by(self.model.deadline.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def search_by_lesson_name(
        self, 
        lesson_name: str
    ) -> Sequence[Task]:
        """Поиск задач по названию занятия (частичное совпадение)"""
        statement = select(self.model).where(
            self.model.lesson_name.ilike(f"%{lesson_name}%")
        ).order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_tasks_with_filters(
        self,
        specialty: Optional[str] = None,
        course: Optional[int] = None,
        lesson_type: Optional[LessonType] = None,
        checker_id: Optional[int] = None
    ) -> Sequence[Task]:
        """Получить задачи с множественными фильтрами"""
        statement = select(self.model)
        
        if specialty:
            statement = statement.where(self.model.specialty == specialty)
        if course:
            statement = statement.where(self.model.course == course)
        if lesson_type:
            statement = statement.where(self.model.lesson_type == lesson_type)
        if checker_id:
            statement = statement.where(self.model.checker == checker_id)
        
        statement = statement.order_by(self.model.deadline)
        result = await self.session.execute(statement)
        return result.scalars().all()


def get_task_repo(session: AsyncSession = Depends(get_db)) -> TaskRepository:
    """Dependency для получения репозитория задач"""
    return TaskRepository(session)
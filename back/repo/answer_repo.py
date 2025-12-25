from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Sequence, Optional
from datetime import datetime

from ..repo import BaseRepository
from ..models import Answer
from ..utils import get_db
from ..enums import AnswerStatus


class AnswerRepository(BaseRepository[Answer]):
    """Репозиторий для работы с ответами на задания"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Answer, session)

    async def get_by_task_and_student(self, task_id: int, student_id: int) -> Answer | None:
        """Получить ответ студента на конкретное задание"""
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.student_id == student_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_by_task(self, task_id: int) -> Sequence[Answer]:
        """Получить все ответы на конкретное задание"""
        statement = select(self.model).where(
            self.model.task_id == task_id
        ).order_by(self.model.add_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_all_by_student(self, student_id: int) -> Sequence[Answer]:
        """Получить все ответы конкретного студента"""
        statement = select(self.model).where(
            self.model.student_id == student_id
        ).order_by(self.model.add_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_status(self, status: AnswerStatus) -> Sequence[Answer]:
        """Получить все ответы с определенным статусом"""
        statement = select(self.model).where(
            self.model.status == status
        ).order_by(self.model.add_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_submitted_for_task(self, task_id: int) -> Sequence[Answer]:
        """Получить все отправленные на проверку ответы для задания"""
        statement = select(self.model).where(
            self.model.task_id == task_id,
            self.model.status == AnswerStatus.SUBMITTED
        ).order_by(self.model.add_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_graded_for_student(self, student_id: int) -> Sequence[Answer]:
        """Получить все оцененные ответы студента"""
        statement = select(self.model).where(
            self.model.student_id == student_id,
            self.model.status == AnswerStatus.GRADED
        ).order_by(self.model.graded_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_by_task(self, task_id: int) -> int:
        """Подсчитать количество ответов на задание"""
        statement = select(self.model).where(self.model.task_id == task_id)
        result = await self.session.execute(statement)
        return len(result.scalars().all())

    async def get_answers_with_filters(
        self,
        task_id: Optional[int] = None,
        student_id: Optional[int] = None,
        status: Optional[AnswerStatus] = None,
        grade_min: Optional[int] = None,
        grade_max: Optional[int] = None
    ) -> Sequence[Answer]:
        """Получить ответы с множественными фильтрами"""
        statement = select(self.model)
        
        if task_id:
            statement = statement.where(self.model.task_id == task_id)
        if student_id:
            statement = statement.where(self.model.student_id == student_id)
        if status:
            statement = statement.where(self.model.status == status)
        if grade_min is not None:
            statement = statement.where(self.model.grade >= grade_min)
        if grade_max is not None:
            statement = statement.where(self.model.grade <= grade_max)
        
        statement = statement.order_by(self.model.add_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()


def get_answer_repo(session: AsyncSession = Depends(get_db)) -> AnswerRepository:
    """Dependency для получения репозитория ответов"""
    return AnswerRepository(session)
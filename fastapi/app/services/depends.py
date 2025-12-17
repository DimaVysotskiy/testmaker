from typing_extensions import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from core import sessionmanager
from fastapi import Depends
from typing import Annotated
from services.user_service import UserService


async def get_user_service(self, session: Annotated[AsyncSession, Depends(sessionmanager.get_session)]) -> UserService:
        """Dependency для получения сервиса пользователей"""
        return UserService(session)
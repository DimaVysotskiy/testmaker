# repositories/user_repo.py
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from ..repo import BaseRepository
from ..entities.models import User
from ..utils import get_db, password_checker


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями"""
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_username(self, username: str) -> User | None:
        """Получить пользователя по username"""
        statement = select(self.model).where(self.model.username == username)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Получить пользователя по email"""
        statement = select(self.model).where(self.model.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_oauth(self, provider: str, oauth_id: str) -> User | None:
        """Получить пользователя по OAuth провайдеру и ID"""
        statement = select(self.model).where(
            self.model.oauth_provider == provider,
            self.model.oauth_id == oauth_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
    
    async def authenticate_user(self, username: str, password: str) -> User | None:
        """Аутентификация пользователя по username и паролю"""
        user = await self.get_by_username(username)
        if not user:
            return None
        if not user.hashed_password:
            # Пользователь зарегистрирован через OAuth
            return None
        if not password_checker.verify_password(password, user.hashed_password):
            return None
        return user


def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency для получения репозитория пользователей"""
    return UserRepository(session)
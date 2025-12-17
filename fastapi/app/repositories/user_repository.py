from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user import User
from app.models.enums import RoleInSystem


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user(
        self, 
        user_login: str, 
        password_hash: str, 
        user_role: RoleInSystem
    ) -> User:
        """Создает нового пользователя в базе данных"""
        new_user = User(
            user_login=user_login,
            password_hash=password_hash,
            user_role=user_role
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user
    
    async def get_user_by_login(self, user_login: str) -> Optional[User]:
        """Получает пользователя по логину"""
        result = await self.session.execute(
            select(User).where(User.user_login == user_login)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def user_exists(self, user_login: str) -> bool:
        """Проверяет существование пользователя по логину"""
        user = await self.get_user_by_login(user_login)
        return user is not None
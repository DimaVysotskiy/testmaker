from typing import List, Optional, Dict, Any
from fastapi import Depends, HTTPException, status

from ..repo import get_user_repo, UserRepository
from ..entities.models import User
from ..entities.schemas import UserCreate, UserBase
from ..entities.enums import UserRole
from ..utils import password_checker


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_user_by_id(self, user_id: int) -> User:
        """Получить пользователя по ID"""
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    async def get_all_users(self) -> List[User]:
        """Получить всех пользователей"""
        return await self.user_repo.get_all()
    
    async def get_user_by_username(self, username: str) -> User:
        """Получить пользователя по username"""
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    async def get_user_by_email(self, email: str) -> User:
        """Получить пользователя по email"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        # Проверка уникальности username
        if user_data.username:
            existing_user = await self.user_repo.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
        
        # Проверка уникальности email
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Хешируем пароль
        hashed_password = password_checker.get_password_hash(user_data.password)
        
        # Подготавливаем данные
        user_dict = user_data.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        
        return await self.user_repo.create(user_dict)
    
    async def update_user_profile(
        self, 
        user: User, 
        user_data: UserBase
    ) -> User:
        """Обновить профиль пользователя"""
        update_dict = {}
        
        # Проверка уникальности username
        if user_data.username and user_data.username != user.username:
            existing_user = await self.user_repo.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            update_dict["username"] = user_data.username
        
        # Проверка уникальности email
        if user_data.email != user.email:
            existing_user = await self.user_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            update_dict["email"] = user_data.email
            update_dict["is_email_verified"] = False
        
        if user_data.full_name is not None:
            update_dict["full_name"] = user_data.full_name
        
        if update_dict:
            return await self.user_repo.update(user.id, update_dict)
        
        return user
    
    async def update_user_by_admin(
        self,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        is_email_verified: Optional[bool] = None
    ) -> User:
        """Обновить пользователя администратором"""
        user = await self.get_user_by_id(user_id)
        
        update_dict = {}
        
        # Проверка уникальности username
        if username and username != user.username:
            existing_user = await self.user_repo.get_by_username(username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            update_dict["username"] = username
        
        # Проверка уникальности email
        if email and email != user.email:
            existing_user = await self.user_repo.get_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            update_dict["email"] = email
        
        if full_name is not None:
            update_dict["full_name"] = full_name
        if role is not None:
            update_dict["role"] = role
        if is_active is not None:
            update_dict["is_active"] = is_active
        if is_verified is not None:
            update_dict["is_verified"] = is_verified
        if is_email_verified is not None:
            update_dict["is_email_verified"] = is_email_verified
        
        if update_dict:
            return await self.user_repo.update(user_id, update_dict)
        
        return user
    
    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str
    ) -> Dict[str, str]:
        """Изменить пароль пользователя"""
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change password for OAuth users"
            )
        
        if not password_checker.verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        new_hashed_password = password_checker.get_password_hash(new_password)
        await self.user_repo.update(user.id, {"hashed_password": new_hashed_password})
        
        return {"message": "Password successfully changed"}
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> Dict[str, str]:
        """Сбросить пароль пользователя (admin)"""
        user = await self.get_user_by_id(user_id)
        
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reset password for OAuth users"
            )
        
        new_hashed_password = password_checker.get_password_hash(new_password)
        await self.user_repo.update(user_id, {"hashed_password": new_hashed_password})
        
        return {"message": f"Password for user {user.username} successfully reset"}
    
    async def delete_user(self, user_id: int) -> None:
        """Удалить пользователя"""
        user = await self.get_user_by_id(user_id)
        await self.user_repo.delete(user_id)
    
    async def delete_own_account(self, user: User, password: str) -> None:
        """Удалить свой аккаунт"""
        if user.hashed_password:
            if not password_checker.verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect password"
                )
        
        await self.user_repo.delete(user.id)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """Dependency для получения сервиса пользователей"""
    return UserService(user_repo)
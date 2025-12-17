from typing_extensions import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import Optional
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, LoginRequest, AuthResponse
from app.models.enums import RoleInSystem
from core.password import hash_password, verify_password
from core.jwt import create_jwt_token
from core import sessionmanager
from fastapi import Depends
from typing import Annotated


class UserService:
    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Создает нового пользователя с валидацией"""
        # Проверяем, существует ли пользователь с таким логином
        if await self.repository.user_exists(user_data.user_login):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким логином уже существует"
            )
        
        # Хешируем пароль
        password_hash = hash_password(user_data.password)
        
        # Создаем пользователя
        user = await self.repository.create_user(
            user_login=user_data.user_login,
            password_hash=password_hash,
            user_role=user_data.user_role
        )
        
        return UserResponse.model_validate(user)
    
    async def get_user_by_login(self, user_login: str) -> Optional[UserResponse]:
        """Получает пользователя по логину"""
        user = await self.repository.get_user_by_login(user_login)
        if not user:
            return None
        
        return UserResponse.model_validate(user)
    
    async def authenticate_user(self, login_data: LoginRequest) -> AuthResponse:
        """
        Аутентифицирует пользователя и генерирует JWT токен.
        
        Raises:
            HTTPException: Если пользователь не найден или пароль неверный
        """
        # Получаем пользователя по логину
        user = await self.repository.get_user_by_login(login_data.user_login)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
        
        # Проверяем пароль
        password_hash: str = user.password_hash  # type: ignore
        if not verify_password(login_data.password, password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
        
        # Генерируем JWT токен
        user_id: int = user.id  # type: ignore
        user_role: RoleInSystem = user.user_role  # type: ignore
        access_token = create_jwt_token(user_id, user_role)
        
        # Возвращаем токен и данные пользователя
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )


async def get_user_service(session: Annotated[AsyncSession, Depends(sessionmanager.get_session)]) -> UserService:
        """Dependency для получения сервиса пользователей"""
        return UserService(session)
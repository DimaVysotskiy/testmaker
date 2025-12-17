from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from core.database import sessionmanager
from core.jwt import role_required
from app.models.enums import RoleInSystem
from app.schemas.user import UserCreate, UserResponse, LoginRequest, AuthResponse
from app.services.user_service import UserService, get_user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Авторизация пользователя",
    description="Аутентифицирует пользователя и возвращает JWT токен"
)
async def login(
    login_data: LoginRequest,
    service: Annotated[UserService, Depends(get_user_service)]
) -> AuthResponse:
    """
    Аутентифицирует пользователя по логину и паролю.
    
    Возвращает:
    - access_token: JWT токен для авторизованных запросов
    - token_type: Тип токена (bearer)
    - user: Данные авторизованного пользователя
    """
    return await service.authenticate_user(login_data)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать нового пользователя",
    description="Создает нового пользователя в системе. Доступно только для администраторов."
)
async def create_user(
    user_data: UserCreate,
    service: Annotated[UserService, Depends(get_user_service)],
    token: Annotated[dict, Depends(role_required([RoleInSystem.ADMIN]))]
) -> UserResponse:
    """
    Создает нового пользователя в системе.
    
    Требуется JWT токен администратора в заголовке Authorization.
    """
    return await service.create_user(user_data)


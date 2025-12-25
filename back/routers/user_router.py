from fastapi import APIRouter, Depends, status
from typing import Annotated, List, Optional

from ..entities.schemas import User, UserCreate, UserBase
from ..services import get_user_service, UserService
from ..utils import get_current_active_user, require_roles
from ..entities.enums import UserRole


user_router = APIRouter(prefix="/user", tags=["user"])


# GET операции
@user_router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Получить информацию о текущем пользователе"""
    return current_user


@user_router.get(
    "/{user_id}",
    response_model=User,
    summary="Получение пользователя по ID",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Получить пользователя по ID. Только для администраторов."""
    return await user_service.get_user_by_id(user_id)


@user_router.get(
    "/",
    response_model=List[User],
    summary="Получение списка всех пользователей",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_all_users(
    user_service: UserService = Depends(get_user_service)
):
    """Получить список всех пользователей. Только для администраторов."""
    return await user_service.get_all_users()


@user_router.get(
    "/username/{username}",
    response_model=User,
    summary="Получение пользователя по username",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_user_by_username(
    username: str,
    user_service: UserService = Depends(get_user_service)
):
    """Получить пользователя по username. Только для администраторов."""
    return await user_service.get_user_by_username(username)


@user_router.get(
    "/email/{email}",
    response_model=User,
    summary="Получение пользователя по email",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_user_by_email(
    email: str,
    user_service: UserService = Depends(get_user_service)
):
    """Получить пользователя по email. Только для администраторов."""
    return await user_service.get_user_by_email(email)


# POST операции
@user_router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового пользователя",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Создать нового пользователя. Только для администраторов.
    Проверяет уникальность username и email.
    """
    return await user_service.create_user(user_data)


# PUT операции
@user_router.put(
    "/me",
    response_model=User,
    summary="Обновление своего профиля"
)
async def update_my_profile(
    user_data: UserBase,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: UserService = Depends(get_user_service)
):
    """
    Обновить свой профиль. Пользователь может изменить свои данные,
    кроме роли и статусов активности/верификации.
    """
    return await user_service.update_user_profile(current_user, user_data)


@user_router.put(
    "/{user_id}",
    response_model=User,
    summary="Обновление пользователя администратором",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def update_user(
    user_id: int,
    email: Optional[str] = None,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    is_email_verified: Optional[bool] = None,
    user_service: UserService = Depends(get_user_service)
):
    """
    Обновить пользователя. Только для администраторов.
    Администратор может изменять любые поля, включая роль и статусы.
    """
    return await user_service.update_user_by_admin(
        user_id=user_id,
        email=email,
        username=username,
        full_name=full_name,
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        is_email_verified=is_email_verified
    )


@user_router.put(
    "/me/password",
    summary="Изменение своего пароля"
)
async def change_my_password(
    old_password: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_service: UserService = Depends(get_user_service)
):
    """
    Изменить свой пароль. Требуется текущий пароль для подтверждения.
    """
    return await user_service.change_password(current_user, old_password, new_password)


@user_router.put(
    "/{user_id}/password",
    summary="Сброс пароля пользователя администратором",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def reset_user_password(
    user_id: int,
    new_password: str,
    user_service: UserService = Depends(get_user_service)
):
    """
    Сбросить пароль пользователя. Только для администраторов.
    """
    return await user_service.reset_password(user_id, new_password)


# DELETE операции
@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Удалить пользователя. Только для администраторов.
    Внимание: это удалит пользователя и все связанные с ним данные.
    """
    await user_service.delete_user(user_id)
    return None
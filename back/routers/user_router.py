from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List, Optional

from ..entities.schemas import User, UserCreate, UserBase
from ..repo import get_user_repo
from ..utils import get_current_active_user, require_roles, password_checker
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
    user_repo = Depends(get_user_repo)
):
    """Получить пользователя по ID. Только для администраторов."""
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.get(
    "/",
    response_model=List[User],
    summary="Получение списка всех пользователей",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_all_users(
    user_repo = Depends(get_user_repo)
):
    """Получить список всех пользователей. Только для администраторов."""
    users = await user_repo.get_all()
    return users


@user_router.get(
    "/username/{username}",
    response_model=User,
    summary="Получение пользователя по username",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_user_by_username(
    username: str,
    user_repo = Depends(get_user_repo)
):
    """Получить пользователя по username. Только для администраторов."""
    user = await user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@user_router.get(
    "/email/{email}",
    response_model=User,
    summary="Получение пользователя по email",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def get_user_by_email(
    email: str,
    user_repo = Depends(get_user_repo)
):
    """Получить пользователя по email. Только для администраторов."""
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


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
    user_repo = Depends(get_user_repo)
):
    """
    Создать нового пользователя. Только для администраторов.
    Проверяет уникальность username и email.
    """
    # Проверка уникальности username
    if user_data.username:
        existing_user = await user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    # Проверка уникальности email
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Хешируем пароль
    hashed_password = password_checker.get_password_hash(user_data.password)
    
    # Подготавливаем данные для создания
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["hashed_password"] = hashed_password
    
    # Создаем пользователя
    user = await user_repo.create(user_dict)
    return user


# PUT операции
@user_router.put(
    "/me",
    response_model=User,
    summary="Обновление своего профиля"
)
async def update_my_profile(
    user_data: UserBase,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_repo = Depends(get_user_repo)
):
    """
    Обновить свой профиль. Пользователь может изменить свои данные,
    кроме роли и статусов активности/верификации.
    """
    update_dict = {}
    
    # Проверка уникальности username при изменении
    if user_data.username and user_data.username != current_user.username:
        existing_user = await user_repo.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        update_dict["username"] = user_data.username
    
    # Проверка уникальности email при изменении
    if user_data.email != current_user.email:
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        update_dict["email"] = user_data.email
        update_dict["is_email_verified"] = False  # Требуется повторная верификация

    
    if update_dict:
        user = await user_repo.update(current_user.id, update_dict)
        return user
    
    return current_user


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
    user_repo = Depends(get_user_repo)
):
    """
    Обновить пользователя. Только для администраторов.
    Администратор может изменять любые поля, включая роль и статусы.
    """
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_dict = {}
    
    # Проверка уникальности username
    if username and username != user.username:
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        update_dict["username"] = username
    
    # Проверка уникальности email
    if email and email != user.email:
        existing_user = await user_repo.get_by_email(email)
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
        user = await user_repo.update(user_id, update_dict)
    
    return user


@user_router.put(
    "/me/password",
    summary="Изменение своего пароля"
)
async def change_my_password(
    old_password: str,
    new_password: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_repo = Depends(get_user_repo)
):
    """
    Изменить свой пароль. Требуется текущий пароль для подтверждения.
    """
    # Проверка, что пользователь не OAuth
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth users"
        )
    
    # Проверка старого пароля
    if not password_checker.verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Хешируем новый пароль
    new_hashed_password = password_checker.get_password_hash(new_password)
    
    # Обновляем пароль
    await user_repo.update(current_user.id, {"hashed_password": new_hashed_password})
    
    return {"message": "Password successfully changed"}


@user_router.put(
    "/{user_id}/password",
    summary="Сброс пароля пользователя администратором",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def reset_user_password(
    user_id: int,
    new_password: str,
    user_repo = Depends(get_user_repo)
):
    """
    Сбросить пароль пользователя. Только для администраторов.
    """
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Проверка, что пользователь не OAuth
    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reset password for OAuth users"
        )
    
    # Хешируем новый пароль
    new_hashed_password = password_checker.get_password_hash(new_password)
    
    # Обновляем пароль
    await user_repo.update(user_id, {"hashed_password": new_hashed_password})
    
    return {"message": f"Password for user {user.username} successfully reset"}


# DELETE операции
@user_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя",
    dependencies=[Depends(require_roles(UserRole.ADMIN))]
)
async def delete_user(
    user_id: int,
    user_repo = Depends(get_user_repo)
):
    """
    Удалить пользователя. Только для администраторов.
    Внимание: это удалит пользователя и все связанные с ним данные.
    """
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_repo.delete(user_id)
    return None


@user_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление своего аккаунта"
)
async def delete_my_account(
    password: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_repo = Depends(get_user_repo)
):
    """
    Удалить свой аккаунт. Требуется подтверждение паролем.
    Внимание: это действие необратимо и удалит все ваши данные.
    """
    # Проверка пароля для подтверждения
    if current_user.hashed_password:
        if not password_checker.verify_password(password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
    
    await user_repo.delete(current_user.id)
    return None
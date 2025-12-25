from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import Annotated, List, Optional
from datetime import datetime

from ..entities.schemas import Task, User
from ..services import get_task_service, TaskService
from ..utils import get_current_active_user, require_roles
from ..entities.enums import UserRole, LessonType


task_router = APIRouter(prefix="/tasks", tags=["tasks"])


# POST
@task_router.post(
    "/",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой задачи с файлами",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def create_task(
    title: str,
    description: str,
    lesson_name: str,
    lesson_type: LessonType,
    specialty: str,
    course: int,
    deadline: Optional[datetime] = None, 
    files: Annotated[List[UploadFile], File(description="На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить 'Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    photos: Annotated[List[UploadFile], File(description="На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить 'Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Создать новую задачу с возможностью загрузки файлов и фото.
    """
    return await task_service.create_task(
        title=title,
        description=description,
        lesson_name=lesson_name,
        lesson_type=lesson_type,
        specialty=specialty,
        course=course,
        current_user=current_user,
        deadline=deadline,
        files=files,
        photos=photos
    )


# GET
@task_router.get(
    "/{task_id}",
    response_model=Task,
    summary="Получение задачи по ID"
)
async def get_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Получить задачу по её ID.
    """
    return await task_service.get_task_by_id(task_id)


# PUT
@task_router.put(
    "/{task_id}",
    response_model=Task,
    summary="Обновление задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    lesson_name: Optional[str] = None,
    lesson_type: Optional[LessonType] = None,
    specialty: Optional[str] = None,
    course: Optional[int] = None,
    deadline: Optional[datetime] = None,
    files: Annotated[List[UploadFile], File(description="Новые файлы для добавления. Старые файлы сохраняются.")] = [],
    photos: Annotated[List[UploadFile], File(description="Новые фото для добавления. Старые фото сохраняются.")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_service: TaskService = Depends(get_task_service)
):
    """
    Обновить задачу. Файлы и фото добавляются к существующим.
    Только создатель задачи или admin может её обновить.
    """
    return await task_service.update_task(
        task_id=task_id,
        current_user=current_user,
        title=title,
        description=description,
        lesson_name=lesson_name,
        lesson_type=lesson_type,
        specialty=specialty,
        course=course,
        deadline=deadline,
        files=files,
        photos=photos
    )


# DELETE
@task_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    task_service: TaskService = Depends(get_task_service)
):
    """
    Удалить задачу и все связанные с ней файлы из MinIO.
    Только создатель задачи или admin может её удалить.
    """
    await task_service.delete_task(task_id, current_user)
    return None


@task_router.delete(
    "/{task_id}/files/{file_name}",
    response_model=Task,
    summary="Удаление конкретного файла из задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task_file(
    task_id: int,
    file_name: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    task_service: TaskService = Depends(get_task_service)
):
    """
    Удалить конкретный файл из задачи.
    """
    return await task_service.delete_task_file(task_id, file_name, current_user)


@task_router.delete(
    "/{task_id}/photos/{photo_name}",
    response_model=Task,
    summary="Удаление конкретного фото из задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task_photo(
    task_id: int,
    photo_name: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    task_service: TaskService = Depends(get_task_service)
):
    """
    Удалить конкретное фото из задачи.
    """
    return await task_service.delete_task_photo(task_id, photo_name, current_user)
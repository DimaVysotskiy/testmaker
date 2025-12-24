from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Annotated, List, Optional
from datetime import datetime
import uuid
import json

from ..schemas import Task, TaskUpdate, User
from ..repo import get_task_repo
from ..models import Task as TaskModel
from ..utils import get_current_active_user, require_roles, get_minio, MinioManager
from ..enums import UserRole, LessonType


task_router = APIRouter(prefix="/tasks", tags=["tasks"])


@task_router.post(
    "/",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой задачи с файлами",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def create_task(
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    lesson_name: Annotated[str, Form()],
    lesson_type: Annotated[LessonType, Form()],
    checker: Annotated[int, Form()],
    specialty: Annotated[str, Form()],
    course: Annotated[int, Form()],
    deadline: Annotated[datetime, Form()],
    files: Optional[List[UploadFile]] = File(None),
    photos: Optional[List[UploadFile]] = File(None),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Создать новую задачу с возможностью загрузки файлов и фото.
    Доступно только для учителей и администраторов.
    """
    
    # Проверяем, что задача с таким названием не существует
    existing_task = await task_repo.get_by_title(title)
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task with this title already exists"
        )
    
    # Подготавливаем данные для создания задачи
    task_data = {
        "title": title,
        "description": description,
        "lesson_name": lesson_name,
        "lesson_type": lesson_type,
        "checker": checker,
        "specialty": specialty,
        "course": course,
        "deadline": deadline,
        "file_urls": [],
        "photo_urls": []
    }
    
    # Создаем задачу сначала, чтобы получить ID
    task = await task_repo.create(task_data)
    
    # Загружаем файлы если есть
    if files:
        file_urls = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            object_name = f"tasks/{task.id}/files/{file_id}.{extension}" if extension else f"tasks/{task.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)
            file_urls.append(file_url)
        
        task_data["file_urls"] = file_urls
    
    # Загружаем фото если есть
    if photos:
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        photo_urls = []
        
        for photo in photos:
            if photo.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {photo.filename} is not an image"
                )
            
            file_id = str(uuid.uuid4())
            extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
            object_name = f"tasks/{task.id}/photos/{file_id}.{extension}"
            
            photo_url = await minio.upload_file(photo, object_name)
            photo_urls.append(photo_url)
        
        task_data["photo_urls"] = photo_urls
    
    # Обновляем задачу с URL файлов
    if files or photos:
        task = await task_repo.update(task.id, {
            "file_urls": task_data.get("file_urls"),
            "photo_urls": task_data.get("photo_urls")
        })
    
    return task


@task_router.get(
    "/",
    response_model=List[Task],
    summary="Получить список задач с фильтрами"
)
async def get_tasks(
    specialty: Optional[str] = None,
    course: Optional[int] = None,
    lesson_type: Optional[LessonType] = None,
    checker_id: Optional[int] = None,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить список всех задач с возможностью фильтрации."""
    
    tasks = await task_repo.get_tasks_with_filters(
        specialty=specialty,
        course=course,
        lesson_type=lesson_type,
        checker_id=checker_id
    )
    return tasks


@task_router.get(
    "/{task_id}",
    response_model=Task,
    summary="Получить задачу по ID"
)
async def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить конкретную задачу по её ID."""
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@task_router.get(
    "/specialty/{specialty}/course/{course}",
    response_model=List[Task],
    summary="Получить задачи по специальности и курсу"
)
async def get_tasks_by_specialty_and_course(
    specialty: str,
    course: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить все задачи для конкретной специальности и курса."""
    
    tasks = await task_repo.get_by_specialty_and_course(specialty, course)
    return tasks


@task_router.get(
    "/specialty/{specialty}/course/{course}/upcoming",
    response_model=List[Task],
    summary="Получить предстоящие задачи"
)
async def get_upcoming_tasks(
    specialty: str,
    course: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить задачи с дедлайном в будущем."""
    
    tasks = await task_repo.get_upcoming_tasks(specialty, course)
    return tasks


@task_router.get(
    "/specialty/{specialty}/course/{course}/overdue",
    response_model=List[Task],
    summary="Получить просроченные задачи"
)
async def get_overdue_tasks(
    specialty: str,
    course: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить задачи с истекшим дедлайном."""
    
    tasks = await task_repo.get_overdue_tasks(specialty, course)
    return tasks


@task_router.get(
    "/lesson-type/{lesson_type}",
    response_model=List[Task],
    summary="Получить задачи по типу занятия"
)
async def get_tasks_by_lesson_type(
    lesson_type: LessonType,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить все задачи определенного типа (лекция, практика, лаб. работа)."""
    
    tasks = await task_repo.get_by_lesson_type(lesson_type)
    return tasks


@task_router.get(
    "/checker/{checker_id}",
    response_model=List[Task],
    summary="Получить задачи проверяющего"
)
async def get_tasks_by_checker(
    checker_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Получить все задачи, назначенные определенному проверяющему."""
    
    tasks = await task_repo.get_by_checker(checker_id)
    return tasks


@task_router.get(
    "/search/",
    response_model=List[Task],
    summary="Поиск задач по названию занятия"
)
async def search_tasks(
    lesson_name: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Поиск задач по названию занятия (частичное совпадение)."""
    
    tasks = await task_repo.search_by_lesson_name(lesson_name)
    return tasks


@task_router.put(
    "/{task_id}",
    response_model=Task,
    summary="Обновить задачу",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Обновить существующую задачу. Доступно только для учителей и администраторов."""
    
    # Проверяем существование задачи
    existing_task = await task_repo.get(task_id)
    if not existing_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Если обновляется название, проверяем уникальность
    if task_data.title and task_data.title != existing_task.title:
        title_exists = await task_repo.get_by_title(task_data.title)
        if title_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task with this title already exists"
            )
    
    # Обновляем только переданные поля
    update_data = task_data.model_dump(exclude_unset=True)
    task = await task_repo.update(task_id, update_data)
    return task


@task_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo)
):
    """Удалить задачу. Доступно только для учителей и администраторов."""
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    await task_repo.delete(task_id)
    return None


@task_router.post(
    "/{task_id}/upload-files",
    response_model=Task,
    summary="Добавить файлы к существующей задаче",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def upload_task_files(
    task_id: int,
    files: List[UploadFile] = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """Добавить дополнительные файлы к существующей задаче."""
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Загружаем файлы в MinIO
    file_urls = []
    for file in files:
        file_id = str(uuid.uuid4())
        extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        object_name = f"tasks/{task_id}/files/{file_id}.{extension}" if extension else f"tasks/{task_id}/files/{file_id}"
        
        file_url = await minio.upload_file(file, object_name)
        file_urls.append(file_url)
    
    # Обновляем задачу с новыми URL файлов
    existing_urls = task.file_urls or []
    updated_urls = existing_urls + file_urls
    
    updated_task = await task_repo.update(task_id, {"file_urls": updated_urls})
    return updated_task


@task_router.post(
    "/{task_id}/upload-photos",
    response_model=Task,
    summary="Добавить фото к существующей задаче",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def upload_task_photos(
    task_id: int,
    photos: List[UploadFile] = File(...),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """Добавить дополнительные фотографии к существующей задаче."""
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Проверяем, что файлы являются изображениями
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    photo_urls = []
    for photo in photos:
        if photo.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {photo.filename} is not an image"
            )
        
        file_id = str(uuid.uuid4())
        extension = photo.filename.split('.')[-1] if '.' in photo.filename else 'jpg'
        object_name = f"tasks/{task_id}/photos/{file_id}.{extension}"
        
        photo_url = await minio.upload_file(photo, object_name)
        photo_urls.append(photo_url)
    
    # Обновляем задачу с новыми URL фото
    existing_urls = task.photo_urls or []
    updated_urls = existing_urls + photo_urls
    
    updated_task = await task_repo.update(task_id, {"photo_urls": updated_urls})
    return updated_task


@task_router.delete(
    "/{task_id}/files",
    response_model=Task,
    summary="Удалить файл из задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task_file(
    task_id: int,
    file_url: str,
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo=Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """Удалить файл из задачи."""
    
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if not task.file_urls or file_url not in task.file_urls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in task"
        )
    
    # Извлекаем object_name из URL
    # Предполагается, что URL имеет формат: http://host:port/bucket/object_name
    object_name = file_url.split('/', 4)[-1] if '/' in file_url else file_url
    
    # Удаляем из MinIO
    await minio.delete_file(object_name)
    
    # Обновляем список URL
    updated_urls = [url for url in task.file_urls if url != file_url]
    updated_task = await task_repo.update(task_id, {"file_urls": updated_urls})
    
    return updated_task
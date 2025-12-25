from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Annotated, List, Optional
from datetime import datetime, timedelta
import uuid

from ..schemas import Task, TaskUpdate, User
from ..repo import get_task_repo
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
    title: str,
    description: str,
    lesson_name: str,
    lesson_type: LessonType,
    specialty: str,
    course: int,
    deadline: Optional[datetime] = None, 
    files: Annotated[List[UploadFile], File(description=f"На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    photos: Annotated[List[UploadFile], File(description=f"На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Создать новую задачу с возможностью загрузки файлов и фото.
    """
    # Проверяем, что задача с таким названием не существует
    existing_task = await task_repo.get_by_title(title)
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task with this title already exists"
        )
    
    # Подготавливаем базовые данные для создания задачи
    task_data = {
        "title": title,
        "description": description,
        "lesson_name": lesson_name,
        "lesson_type": lesson_type,
        "checker": current_user.id,
        "specialty": specialty,
        "course": course,
        "deadline": deadline,
        "files_metadata": [],
        "photos_metadata": []
    }
    
    # Создаем задачу сначала, чтобы получить ID
    task = await task_repo.create(task_data)
    
    # Загружаем файлы если есть
    if files:
        files_metadata = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            print(extension)
            object_name = f"tasks/{task.id}/files/{file_id}.{extension}" if extension else f"tasks/{task.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)

            files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        
        # Обновляем задачу с URL файлов
        task = await task_repo.update(task.id, {"files_metadata": files_metadata})
    
    # Загружаем фото если есть
    if photos:
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        photos_metadata = []
        
        for photo in photos:
            if photo.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {photo.filename} is not an image"
                )
            
            file_id = str(uuid.uuid4())
            extension = photo.filename.split('.')[-1] if photo.filename and '.' in photo.filename else 'jpg'
            object_name = f"tasks/{task.id}/photos/{file_id}.{extension}"
            
            photo_url = await minio.upload_file(photo, object_name)

            photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        # Обновляем задачу с URL фото
        task = await task_repo.update(task.id, {"photos_metadata": photos_metadata})
    
    return task

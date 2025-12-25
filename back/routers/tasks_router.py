from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Annotated, List, Optional
from datetime import datetime
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
    files: Annotated[List[UploadFile], File(description="На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить 'Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    photos: Annotated[List[UploadFile], File(description="На фронте или в Swagger не использовать 'Send empty value'. FastAPI сам поставит []. Если оставить 'Send empty value' то при запросе выдаст 422 ошибку.")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Создать новую задачу с возможностью загрузки файлов и фото.
    """
    existing_task = await task_repo.get_by_title(title)
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task with this title already exists"
        )
    
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
    
    task = await task_repo.create(task_data)
    
    if files:
        files_metadata = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"tasks/{task.id}/files/{file_id}.{extension}" if extension else f"tasks/{task.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)
            files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        
        task = await task_repo.update(task.id, {"files_metadata": files_metadata})
    
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
        
        task = await task_repo.update(task.id, {"photos_metadata": photos_metadata})
    
    return task


@task_router.get(
    "/{task_id}",
    response_model=Task,
    summary="Получение задачи по ID"
)
async def get_task(
    task_id: int,
    task_repo = Depends(get_task_repo)
):
    """
    Получить задачу по её ID.
    """
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


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
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Обновить задачу. Файлы и фото добавляются к существующим.
    Только создатель задачи или admin может её обновить.
    """
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Проверка прав: только создатель или admin
    if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this task"
        )
    
    # Проверка уникальности названия, если оно изменяется
    if title and title != task.title:
        existing_task = await task_repo.get_by_title(title)
        if existing_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task with this title already exists"
            )
    
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if lesson_name is not None:
        update_data["lesson_name"] = lesson_name
    if lesson_type is not None:
        update_data["lesson_type"] = lesson_type
    if specialty is not None:
        update_data["specialty"] = specialty
    if course is not None:
        update_data["course"] = course
    if deadline is not None:
        update_data["deadline"] = deadline
    
    # Обработка новых файлов
    if files:
        existing_files = task.files_metadata or []
        new_files_metadata = []
        
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"tasks/{task.id}/files/{file_id}.{extension}" if extension else f"tasks/{task.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)
            new_files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        
        update_data["files_metadata"] = existing_files + new_files_metadata
    
    # Обработка новых фото
    if photos:
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        existing_photos = task.photos_metadata or []
        new_photos_metadata = []
        
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
            new_photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        update_data["photos_metadata"] = existing_photos + new_photos_metadata
    
    if update_data:
        task = await task_repo.update(task_id, update_data)
    
    return task


@task_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление задачи",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Удалить задачу и все связанные с ней файлы из MinIO.
    Только создатель задачи или admin может её удалить.
    """
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Проверка прав
    if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this task"
        )
    
    # Удаляем все файлы из MinIO
    if task.files_metadata:
        for file_meta in task.files_metadata:
            try:
                # Извлекаем object_name из URL
                url = file_meta.get("url", "")
                if url:
                    # URL формат: http://host:port/bucket/object_name
                    object_name = "/".join(url.split("/")[4:])  # Получаем путь после bucket
                    await minio.delete_file(object_name)
            except Exception as e:
                # Логируем, но не прерываем процесс удаления
                print(f"Failed to delete file: {e}")
    
    # Удаляем все фото из MinIO
    if task.photos_metadata:
        for photo_meta in task.photos_metadata:
            try:
                url = photo_meta.get("url", "")
                if url:
                    object_name = "/".join(url.split("/")[4:])
                    await minio.delete_file(object_name)
            except Exception as e:
                print(f"Failed to delete photo: {e}")
    
    # Удаляем задачу из БД
    await task_repo.delete(task_id)
    
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
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Удалить конкретный файл из задачи.
    """
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this task"
        )
    
    if not task.files_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found in this task"
        )
    
    # Находим файл по имени
    file_to_delete = None
    updated_files = []
    
    for file_meta in task.files_metadata:
        if file_meta.get("name") == file_name:
            file_to_delete = file_meta
        else:
            updated_files.append(file_meta)
    
    if not file_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_name}' not found in task"
        )
    
    # Удаляем файл из MinIO
    try:
        url = file_to_delete.get("url", "")
        if url:
            object_name = "/".join(url.split("/")[4:])
            await minio.delete_file(object_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file from storage: {str(e)}"
        )
    
    # Обновляем задачу
    task = await task_repo.update(task_id, {"files_metadata": updated_files})
    
    return task


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
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Удалить конкретное фото из задачи.
    """
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this task"
        )
    
    if not task.photos_metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No photos found in this task"
        )
    
    # Находим фото по имени
    photo_to_delete = None
    updated_photos = []
    
    for photo_meta in task.photos_metadata:
        if photo_meta.get("name") == photo_name:
            photo_to_delete = photo_meta
        else:
            updated_photos.append(photo_meta)
    
    if not photo_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo '{photo_name}' not found in task"
        )
    
    # Удаляем фото из MinIO
    try:
        url = photo_to_delete.get("url", "")
        if url:
            object_name = "/".join(url.split("/")[4:])
            await minio.delete_file(object_name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete photo from storage: {str(e)}"
        )
    
    # Обновляем задачу
    task = await task_repo.update(task_id, {"photos_metadata": updated_photos})
    
    return task
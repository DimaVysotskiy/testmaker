from typing import List, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status, UploadFile
import uuid

from ..repo import get_task_repo, TaskRepository
from ..entities.models import Task, User
from ..entities.enums import UserRole
from ..utils import get_minio, MinioManager


class TaskService:
    """Сервис для работы с задачами"""
    
    def __init__(self, task_repo: TaskRepository, minio: MinioManager):
        self.task_repo = task_repo
        self.minio = minio
    
    async def get_task_by_id(self, task_id: int) -> Task:
        """Получить задачу по ID"""
        task = await self.task_repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        return task
    
    async def create_task(
        self,
        title: str,
        description: str,
        lesson_name: str,
        lesson_type: str,
        specialty: str,
        course: int,
        current_user: User,
        deadline: Optional[datetime] = None,
        files: List[UploadFile] = [],
        photos: List[UploadFile] = []
    ) -> Task:
        """Создать новую задачу"""
        # Проверка уникальности названия
        existing_task = await self.task_repo.get_by_title(title)
        if existing_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task with this title already exists"
            )
        
        # Создаем задачу
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
        
        task = await self.task_repo.create(task_data)
        
        # Загружаем файлы
        if files:
            files_metadata = await self._upload_files(task.id, files, "files")
            task = await self.task_repo.update(task.id, {"files_metadata": files_metadata})
        
        # Загружаем фото
        if photos:
            photos_metadata = await self._upload_photos(task.id, photos)
            task = await self.task_repo.update(task.id, {"photos_metadata": photos_metadata})
        
        return task
    
    async def update_task(
        self,
        task_id: int,
        current_user: User,
        title: Optional[str] = None,
        description: Optional[str] = None,
        lesson_name: Optional[str] = None,
        lesson_type: Optional[str] = None,
        specialty: Optional[str] = None,
        course: Optional[int] = None,
        deadline: Optional[datetime] = None,
        files: List[UploadFile] = [],
        photos: List[UploadFile] = []
    ) -> Task:
        """Обновить задачу"""
        task = await self.get_task_by_id(task_id)
        
        # Проверка прав
        if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this task"
            )
        
        # Проверка уникальности названия
        if title and title != task.title:
            existing_task = await self.task_repo.get_by_title(title)
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
        
        # Добавляем новые файлы
        if files:
            existing_files = task.files_metadata or []
            new_files = await self._upload_files(task.id, files, "files")
            update_data["files_metadata"] = existing_files + new_files
        
        # Добавляем новые фото
        if photos:
            existing_photos = task.photos_metadata or []
            new_photos = await self._upload_photos(task.id, photos)
            update_data["photos_metadata"] = existing_photos + new_photos
        
        if update_data:
            task = await self.task_repo.update(task_id, update_data)
        
        return task
    
    async def delete_task(self, task_id: int, current_user: User) -> None:
        """Удалить задачу"""
        task = await self.get_task_by_id(task_id)
        
        # Проверка прав
        if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this task"
            )
        
        # Удаляем файлы из MinIO
        await self._delete_task_files(task)
        
        # Удаляем задачу
        await self.task_repo.delete(task_id)
    
    async def delete_task_file(
        self,
        task_id: int,
        file_name: str,
        current_user: User
    ) -> Task:
        """Удалить файл из задачи"""
        task = await self.get_task_by_id(task_id)
        
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
        
        # Находим и удаляем файл
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
        
        # Удаляем из MinIO
        await self._delete_file_from_minio(file_to_delete)
        
        return await self.task_repo.update(task_id, {"files_metadata": updated_files})
    
    async def delete_task_photo(
        self,
        task_id: int,
        photo_name: str,
        current_user: User
    ) -> Task:
        """Удалить фото из задачи"""
        task = await self.get_task_by_id(task_id)
        
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
        
        # Находим и удаляем фото
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
        
        # Удаляем из MinIO
        await self._delete_file_from_minio(photo_to_delete)
        
        return await self.task_repo.update(task_id, {"photos_metadata": updated_photos})
    
    # Вспомогательные методы
    async def _upload_files(
        self,
        task_id: int,
        files: List[UploadFile],
        folder: str
    ) -> List[dict]:
        """Загрузить файлы в MinIO"""
        files_metadata = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"tasks/{task_id}/{folder}/{file_id}.{extension}" if extension else f"tasks/{task_id}/{folder}/{file_id}"
            
            file_url = await self.minio.upload_file(file, object_name)
            files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        return files_metadata
    
    async def _upload_photos(
        self,
        task_id: int,
        photos: List[UploadFile]
    ) -> List[dict]:
        """Загрузить фото в MinIO"""
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
            object_name = f"tasks/{task_id}/photos/{file_id}.{extension}"
            
            photo_url = await self.minio.upload_file(photo, object_name)
            photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        return photos_metadata
    
    async def _delete_task_files(self, task: Task) -> None:
        """Удалить все файлы задачи из MinIO"""
        if task.files_metadata:
            for file_meta in task.files_metadata:
                try:
                    await self._delete_file_from_minio(file_meta)
                except Exception as e:
                    print(f"Failed to delete file: {e}")
        
        if task.photos_metadata:
            for photo_meta in task.photos_metadata:
                try:
                    await self._delete_file_from_minio(photo_meta)
                except Exception as e:
                    print(f"Failed to delete photo: {e}")
    
    async def _delete_file_from_minio(self, file_meta: dict) -> None:
        """Удалить файл из MinIO"""
        url = file_meta.get("url", "")
        if url:
            object_name = "/".join(url.split("/")[4:])
            await self.minio.delete_file(object_name)


def get_task_service(
    task_repo: TaskRepository = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
) -> TaskService:
    """Dependency для получения сервиса задач"""
    return TaskService(task_repo, minio)
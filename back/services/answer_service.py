from typing import List, Optional
from datetime import datetime
from fastapi import Depends, HTTPException, status, UploadFile
import uuid

from ..repo import get_answer_repo, get_task_repo, AnswerRepository, TaskRepository
from ..entities.models import Answer, User
from ..entities.schemas import AnswerGrade
from ..entities.enums import UserRole, AnswerStatus
from ..utils import get_minio, MinioManager


class AnswerService:
    """Сервис для работы с ответами на задания"""
    
    def __init__(
        self,
        answer_repo: AnswerRepository,
        task_repo: TaskRepository,
        minio: MinioManager
    ):
        self.answer_repo = answer_repo
        self.task_repo = task_repo
        self.minio = minio
    
    async def get_answer_by_id(
        self,
        answer_id: int,
        current_user: User
    ) -> Answer:
        """
        Получить ответ по ID с проверкой прав доступа.
        Студент видит только свои ответы.
        Преподаватель/admin видит ответы на свои задания.
        """
        answer = await self.answer_repo.get(answer_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Проверка прав доступа
        task = await self.task_repo.get(answer.task_id)
        is_student_owner = answer.student_id == current_user.id
        is_task_checker = task.checker == current_user.id
        is_admin = current_user.role == UserRole.ADMIN
        
        if not (is_student_owner or is_task_checker or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this answer"
            )
        
        return answer
    
    async def get_answers_by_task(
        self,
        task_id: int,
        current_user: User
    ) -> List[Answer]:
        """
        Получить все ответы на задание.
        Только преподаватель-создатель или admin.
        """
        task = await self.task_repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Проверка прав
        if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view answers for this task"
            )
        
        return await self.answer_repo.get_all_by_task(task_id)
    
    async def get_my_answers(self, student_id: int) -> List[Answer]:
        """Получить все свои ответы"""
        return await self.answer_repo.get_all_by_student(student_id)
    
    async def get_answers_by_student(self, student_id: int) -> List[Answer]:
        """Получить все ответы студента (для преподавателя/admin)"""
        return await self.answer_repo.get_all_by_student(student_id)
    
    async def get_answers_with_filters(
        self,
        task_id: Optional[int] = None,
        student_id: Optional[int] = None,
        status: Optional[AnswerStatus] = None,
        grade_min: Optional[int] = None,
        grade_max: Optional[int] = None
    ) -> List[Answer]:
        """Получить ответы с множественными фильтрами"""
        return await self.answer_repo.get_answers_with_filters(
            task_id=task_id,
            student_id=student_id,
            status=status,
            grade_min=grade_min,
            grade_max=grade_max
        )
    
    async def create_answer(
        self,
        task_id: int,
        message: str,
        current_user: User,
        files: List[UploadFile] = [],
        photos: List[UploadFile] = []
    ) -> Answer:
        """
        Создать ответ на задание.
        Студент может отправить только один ответ на задание.
        """
        # Проверяем существование задания
        task = await self.task_repo.get(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Проверяем, не отправлял ли студент уже ответ
        existing_answer = await self.answer_repo.get_by_task_and_student(
            task_id, current_user.id
        )
        if existing_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted an answer for this task"
            )
        
        # Создаем ответ
        answer_data = {
            "task_id": task_id,
            "student_id": current_user.id,
            "message": message,
            "status": AnswerStatus.SUBMITTED,
            "files_metadata": [],
            "photos_metadata": []
        }
        
        answer = await self.answer_repo.create(answer_data)
        
        # Загружаем файлы
        if files:
            files_metadata = await self._upload_files(answer.id, files)
            answer = await self.answer_repo.update(
                answer.id,
                {"files_metadata": files_metadata}
            )
        
        # Загружаем фото
        if photos:
            photos_metadata = await self._upload_photos(answer.id, photos)
            answer = await self.answer_repo.update(
                answer.id,
                {"photos_metadata": photos_metadata}
            )
        
        return answer
    
    async def update_answer(
        self,
        answer_id: int,
        current_user: User,
        message: Optional[str] = None,
        files: List[UploadFile] = [],
        photos: List[UploadFile] = []
    ) -> Answer:
        """
        Обновить ответ.
        Можно только до проверки (статус SUBMITTED).
        """
        answer = await self.answer_repo.get(answer_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Проверка прав
        if answer.student_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this answer"
            )
        
        # Проверка статуса
        if answer.status != AnswerStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update answer that has been graded or returned"
            )
        
        update_data = {}
        if message is not None:
            update_data["message"] = message
        
        # Добавляем новые файлы к существующим
        if files:
            existing_files = answer.files_metadata or []
            new_files = await self._upload_files(answer.id, files)
            update_data["files_metadata"] = existing_files + new_files
        
        # Добавляем новые фото к существующим
        if photos:
            existing_photos = answer.photos_metadata or []
            new_photos = await self._upload_photos(answer.id, photos)
            update_data["photos_metadata"] = existing_photos + new_photos
        
        if update_data:
            answer = await self.answer_repo.update(answer_id, update_data)
        
        return answer
    
    async def grade_answer(
        self,
        answer_id: int,
        grade_data: AnswerGrade,
        current_user: User
    ) -> Answer:
        """
        Выставить оценку за ответ.
        Только преподаватель-создатель задания или admin.
        """
        answer = await self.answer_repo.get(answer_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Проверка прав
        task = await self.task_repo.get(answer.task_id)
        if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to grade this answer"
            )
        
        # Обновляем ответ с оценкой
        update_data = {
            "grade": grade_data.grade,
            "teacher_comment": grade_data.teacher_comment,
            "status": grade_data.status,
            "graded_at": datetime.now()
        }
        
        return await self.answer_repo.update(answer_id, update_data)
    
    async def delete_answer(
        self,
        answer_id: int,
        current_user: User
    ) -> None:
        """
        Удалить ответ.
        Можно только до проверки (статус SUBMITTED).
        """
        answer = await self.answer_repo.get(answer_id)
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Проверка прав
        if answer.student_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this answer"
            )
        
        # Проверка статуса
        if answer.status != AnswerStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete answer that has been graded"
            )
        
        # Удаляем все файлы из MinIO
        await self._delete_answer_files(answer)
        
        # Удаляем ответ из БД
        await self.answer_repo.delete(answer_id)
    
    # ==========================================
    # Вспомогательные методы для работы с файлами
    # ==========================================
    
    async def _upload_files(
        self,
        answer_id: int,
        files: List[UploadFile]
    ) -> List[dict]:
        """Загрузить файлы в MinIO"""
        files_metadata = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"answers/{answer_id}/files/{file_id}.{extension}" if extension else f"answers/{answer_id}/files/{file_id}"
            
            file_url = await self.minio.upload_file(file, object_name)
            files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        return files_metadata
    
    async def _upload_photos(
        self,
        answer_id: int,
        photos: List[UploadFile]
    ) -> List[dict]:
        """Загрузить фото в MinIO с валидацией типов"""
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
            object_name = f"answers/{answer_id}/photos/{file_id}.{extension}"
            
            photo_url = await self.minio.upload_file(photo, object_name)
            photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        return photos_metadata
    
    async def _delete_answer_files(self, answer: Answer) -> None:
        """Удалить все файлы ответа из MinIO"""
        # Удаляем файлы
        if answer.files_metadata:
            for file_meta in answer.files_metadata:
                try:
                    await self._delete_file_from_minio(file_meta)
                except Exception as e:
                    print(f"Failed to delete file: {e}")
        
        # Удаляем фото
        if answer.photos_metadata:
            for photo_meta in answer.photos_metadata:
                try:
                    await self._delete_file_from_minio(photo_meta)
                except Exception as e:
                    print(f"Failed to delete photo: {e}")
    
    async def _delete_file_from_minio(self, file_meta: dict) -> None:
        """Удалить файл из MinIO по метаданным"""
        url = file_meta.get("url", "")
        if url:
            # URL формат: http://host:port/bucket/object_name
            # Извлекаем object_name (путь после bucket)
            object_name = "/".join(url.split("/")[4:])
            await self.minio.delete_file(object_name)


def get_answer_service(
    answer_repo: AnswerRepository = Depends(get_answer_repo),
    task_repo: TaskRepository = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
) -> AnswerService:
    """Dependency для получения сервиса ответов"""
    return AnswerService(answer_repo, task_repo, minio)
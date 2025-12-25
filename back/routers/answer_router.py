from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Annotated, List, Optional
from datetime import datetime
import uuid

from ..entities.schemas import Answer, AnswerGrade, User
from ..repo import get_answer_repo, get_task_repo
from ..utils import get_current_active_user, require_roles, get_minio, MinioManager
from ..entities.enums import UserRole, AnswerStatus


answer_router = APIRouter(prefix="/answers", tags=["answers"])


#get
@answer_router.get(
    "/{answer_id}",
    response_model=Answer,
    summary="Получение ответа по ID"
)
async def get_answer(
    answer_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_repo = Depends(get_answer_repo),
    task_repo = Depends(get_task_repo)
):
    """
    Получить ответ по ID. Студент может видеть только свои ответы.
    Преподаватель/admin видит все ответы на свои задания.
    """
    answer = await answer_repo.get(answer_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Проверка доступа
    task = await task_repo.get(answer.task_id)
    is_student_owner = answer.student_id == current_user.id
    is_task_checker = task.checker == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    
    if not (is_student_owner or is_task_checker or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this answer"
        )
    
    return answer


@answer_router.get(
    "/task/{task_id}",
    response_model=List[Answer],
    summary="Получение всех ответов на задание",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def get_answers_by_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_repo = Depends(get_answer_repo),
    task_repo = Depends(get_task_repo)
):
    """
    Получить все ответы на задание. Только преподаватель-создатель или admin.
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
            detail="You don't have permission to view answers for this task"
        )
    
    answers = await answer_repo.get_all_by_task(task_id)
    return answers


@answer_router.get(
    "/student/me",
    response_model=List[Answer],
    summary="Получение всех моих ответов",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def get_my_answers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_repo = Depends(get_answer_repo)
):
    """
    Получить все свои ответы.
    """
    answers = await answer_repo.get_all_by_student(current_user.id)
    return answers


@answer_router.get(
    "/student/{student_id}",
    response_model=List[Answer],
    summary="Получение всех ответов студента",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def get_answers_by_student(
    student_id: int,
    answer_repo = Depends(get_answer_repo)
):
    """
    Получить все ответы конкретного студента. Только для преподавателей и админов.
    """
    answers = await answer_repo.get_all_by_student(student_id)
    return answers


@answer_router.get(
    "/",
    response_model=List[Answer],
    summary="Получение ответов с фильтрами",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def get_answers_with_filters(
    task_id: Optional[int] = None,
    student_id: Optional[int] = None,
    status: Optional[AnswerStatus] = None,
    grade_min: Optional[int] = None,
    grade_max: Optional[int] = None,
    answer_repo = Depends(get_answer_repo)
):
    """
    Получить ответы с множественными фильтрами.
    """
    answers = await answer_repo.get_answers_with_filters(
        task_id=task_id,
        student_id=student_id,
        status=status,
        grade_min=grade_min,
        grade_max=grade_max
    )
    return answers


#post
@answer_router.post(
    "/",
    response_model=Answer,
    status_code=status.HTTP_201_CREATED,
    summary="Создание ответа на задание",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def create_answer(
    task_id: int,
    message: str,
    files: Annotated[List[UploadFile], File(description="Файлы с ответом")] = [],
    photos: Annotated[List[UploadFile], File(description="Фото с ответом")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    answer_repo = Depends(get_answer_repo),
    task_repo = Depends(get_task_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Создать ответ на задание. Студент может отправить только один ответ на задание.
    """
    # Проверяем существование задания
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Проверяем, не отправлял ли студент уже ответ
    existing_answer = await answer_repo.get_by_task_and_student(task_id, current_user.id)
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
    
    answer = await answer_repo.create(answer_data)
    
    # Загружаем файлы
    if files:
        files_metadata = []
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"answers/{answer.id}/files/{file_id}.{extension}" if extension else f"answers/{answer.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)
            files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        
        answer = await answer_repo.update(answer.id, {"files_metadata": files_metadata})
    
    # Загружаем фото
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
            object_name = f"answers/{answer.id}/photos/{file_id}.{extension}"
            
            photo_url = await minio.upload_file(photo, object_name)
            photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        answer = await answer_repo.update(answer.id, {"photos_metadata": photos_metadata})
    
    return answer


@answer_router.post(
    "/{answer_id}/grade",
    response_model=Answer,
    summary="Выставление оценки за ответ",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def grade_answer(
    answer_id: int,
    grade_data: AnswerGrade,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_repo = Depends(get_answer_repo),
    task_repo = Depends(get_task_repo)
):
    """
    Выставить оценку за ответ. Только преподаватель-создатель задания или admin.
    """
    answer = await answer_repo.get(answer_id)
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Проверка прав
    task = await task_repo.get(answer.task_id)
    if task.checker != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to grade this answer"
        )
    
    # Обновляем ответ
    update_data = {
        "grade": grade_data.grade,
        "teacher_comment": grade_data.teacher_comment,
        "status": grade_data.status,
        "graded_at": datetime.now()
    }
    
    answer = await answer_repo.update(answer_id, update_data)
    return answer


#put
@answer_router.put(
    "/{answer_id}",
    response_model=Answer,
    summary="Обновление ответа студентом",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def update_answer(
    answer_id: int,
    message: Optional[str] = None,
    files: Annotated[List[UploadFile], File(description="Новые файлы для добавления")] = [],
    photos: Annotated[List[UploadFile], File(description="Новые фото для добавления")] = [],
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    answer_repo = Depends(get_answer_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Обновить свой ответ. Можно только до того, как преподаватель проверит (статус SUBMITTED).
    """
    answer = await answer_repo.get(answer_id)
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
    
    # Обработка новых файлов
    if files:
        existing_files = answer.files_metadata or []
        new_files_metadata = []
        
        for file in files:
            file_id = str(uuid.uuid4())
            extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
            object_name = f"answers/{answer.id}/files/{file_id}.{extension}" if extension else f"answers/{answer.id}/files/{file_id}"
            
            file_url = await minio.upload_file(file, object_name)
            new_files_metadata.append({
                "name": file.filename,
                "url": file_url
            })
        
        update_data["files_metadata"] = existing_files + new_files_metadata
    
    # Обработка новых фото
    if photos:
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        existing_photos = answer.photos_metadata or []
        new_photos_metadata = []
        
        for photo in photos:
            if photo.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {photo.filename} is not an image"
                )
            
            file_id = str(uuid.uuid4())
            extension = photo.filename.split('.')[-1] if photo.filename and '.' in photo.filename else 'jpg'
            object_name = f"answers/{answer.id}/photos/{file_id}.{extension}"
            
            photo_url = await minio.upload_file(photo, object_name)
            new_photos_metadata.append({
                "name": photo.filename,
                "url": photo_url
            })
        
        update_data["photos_metadata"] = existing_photos + new_photos_metadata
    
    if update_data:
        answer = await answer_repo.update(answer_id, update_data)
    
    return answer


#delete
@answer_router.delete(
    "/{answer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление ответа",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def delete_answer(
    answer_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_repo = Depends(get_answer_repo),
    minio: MinioManager = Depends(get_minio)
):
    """
    Удалить свой ответ. Можно только до проверки (статус SUBMITTED).
    """
    answer = await answer_repo.get(answer_id)
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
    
    # Удаляем файлы из MinIO
    if answer.files_metadata:
        for file_meta in answer.files_metadata:
            try:
                url = file_meta.get("url", "")
                if url:
                    object_name = "/".join(url.split("/")[4:])
                    await minio.delete_file(object_name)
            except Exception as e:
                print(f"Failed to delete file: {e}")
    
    # Удаляем фото из MinIO
    if answer.photos_metadata:
        for photo_meta in answer.photos_metadata:
            try:
                url = photo_meta.get("url", "")
                if url:
                    object_name = "/".join(url.split("/")[4:])
                    await minio.delete_file(object_name)
            except Exception as e:
                print(f"Failed to delete photo: {e}")
    
    # Удаляем ответ из БД
    await answer_repo.delete(answer_id)
    
    return None
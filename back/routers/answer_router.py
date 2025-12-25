from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import Annotated, List, Optional

from ..entities.schemas import Answer, AnswerGrade, User
from ..services import get_answer_service, AnswerService
from ..utils import get_current_active_user, require_roles
from ..entities.enums import UserRole, AnswerStatus


answer_router = APIRouter(prefix="/answers", tags=["answers"])


# GET
@answer_router.get(
    "/{answer_id}",
    response_model=Answer,
    summary="Получение ответа по ID"
)
async def get_answer(
    answer_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Получить ответ по ID. Студент может видеть только свои ответы.
    Преподаватель/admin видит все ответы на свои задания.
    """
    return await answer_service.get_answer_by_id(answer_id, current_user)


@answer_router.get(
    "/task/{task_id}",
    response_model=List[Answer],
    summary="Получение всех ответов на задание",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def get_answers_by_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Получить все ответы на задание. Только преподаватель-создатель или admin.
    """
    return await answer_service.get_answers_by_task(task_id, current_user)


@answer_router.get(
    "/student/me",
    response_model=List[Answer],
    summary="Получение всех моих ответов",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def get_my_answers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Получить все свои ответы.
    """
    return await answer_service.get_my_answers(current_user.id)


@answer_router.get(
    "/student/{student_id}",
    response_model=List[Answer],
    summary="Получение всех ответов студента",
    dependencies=[Depends(require_roles(UserRole.TEACHER, UserRole.ADMIN))]
)
async def get_answers_by_student(
    student_id: int,
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Получить все ответы конкретного студента. Только для преподавателей и админов.
    """
    return await answer_service.get_answers_by_student(student_id)


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
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Получить ответы с множественными фильтрами.
    """
    return await answer_service.get_answers_with_filters(
        task_id=task_id,
        student_id=student_id,
        status=status,
        grade_min=grade_min,
        grade_max=grade_max
    )


# POST
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
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Создать ответ на задание. Студент может отправить только один ответ на задание.
    """
    return await answer_service.create_answer(
        task_id=task_id,
        message=message,
        current_user=current_user,
        files=files,
        photos=photos
    )


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
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Выставить оценку за ответ. Только преподаватель-создатель задания или admin.
    """
    return await answer_service.grade_answer(answer_id, grade_data, current_user)


# PUT
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
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Обновить свой ответ. Можно только до того, как преподаватель проверит (статус SUBMITTED).
    """
    return await answer_service.update_answer(
        answer_id=answer_id,
        current_user=current_user,
        message=message,
        files=files,
        photos=photos
    )


# DELETE
@answer_router.delete(
    "/{answer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление ответа",
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.ADMIN))]
)
async def delete_answer(
    answer_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    answer_service: AnswerService = Depends(get_answer_service)
):
    """
    Удалить свой ответ. Можно только до проверки (статус SUBMITTED).
    """
    await answer_service.delete_answer(answer_id, current_user)
    return None
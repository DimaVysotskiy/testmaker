from fastapi import APIRouter, File, UploadFile
from typing import Annotated
from ..ai_utils import converter, testmaker


ai_tools_router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


@ai_tools_router.get("/tools-info", summary="Получение информации о доступных AI инструментах.")
def get_ai_tools():
    return {"tools": [
        {"path": "/ai-tools/how_llm_see_my_lecture", "description": "Конвертация файлов лекций в формате PDF или DOCX в Markdown."},
        {"path": "/ai-tools/make_test", "description": "Генерация интерактивного теста по содержанию лекции."}
    ]}


@ai_tools_router.post("/how_llm_see_my_lecture", summary="Конвертация лекции в md через LLM.")
async def how_llm_see_my_lecture(file: UploadFile = File(...)):
    """Принимает файл лекции в формате pdf или docx. LLM возвращает переписанный файл в формате md."""
    md_file = await converter.convert_as_md_file(file)
    return md_file


@ai_tools_router.post("/make_test", summary="Создание теста по лекции через LLM.")
async def make_test(
        file: UploadFile = File(...),
        level: Annotated[str, "Уровень сложности теста: easy, medium, hard"] = "easy",
        count: Annotated[int, "Количество вопросов в тесте"] = 10,
        test_name: Annotated[str, "Название теста"] = "Новый тест"
    ):
    """Принимает файл лекции в формате pdf или docx. LLM возвращает тест в формате json."""
    md_text = await converter.convert_as_md_text(file)
    test = testmaker.make_test(md_text, level=level, count=count, test_name=test_name)
    return test
from fastapi import APIRouter, File, UploadFile
from typing import Annotated
import asyncio
from utils import converter


ai_tools_router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


@ai_tools_router.get("/tools-info", summary="Получение информации о доступных AI инструментах.")
def get_ai_tools():
    return {"tools": [
        {"path": "/ai-tools/how_llm_see_my_lecture", "description": "Конвертация файлов лекций в формате PDF или DOCX в Markdown."}
    ]}


@ai_tools_router.post("/how_llm_see_my_lecture", summary="Конвертация лекции в md через LLM.")
async def how_llm_see_my_lecture(file: UploadFile = File(...)):
    """Принимает файл лекции в формате pdf или docx. LLM возвращает переписанный файл в формате md."""
    md_file = await converter.convert(file)
    return md_file
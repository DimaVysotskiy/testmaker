import pymupdf 
import os
from dotenv import load_dotenv
from ollama import generate
from ollama import GenerateResponse

load_dotenv()

class LectureCleaner:
    def __init__(self):
        self.pdf_path: str = ""

    def _extract_raw_text(self, pdf_path):
        """Приватный метод: корректно открывает переданный путь"""
        doc = pymupdf.open(pdf_path) # ИСПОЛЬЗУЕМ pdf_path, а не "lec1.pdf"
        text = ""
        for page in doc:
            text += "".join(page.get_text()) + "\n"
        return text

    def process_pdf_to_md(self, pdf_path):
        """Основной метод: PDF -> Markdown через LLM"""
        raw_text = self._extract_raw_text(pdf_path)
        
        if len(raw_text) <= 50000:
            # СИСТЕМНАЯ ИНСТРУКЦИЯ: Определяет роль и жесткие правила
            system_instruction = (
                "Ты — профессиональный редактор технических текстов и конспектов. "
                "Твоя задача: преобразовать сырой текст из PDF в идеально структурированный Markdown. "
                "\n\nПРАВИЛА:\n"
                "1. СОХРАННОСТЬ ДАННЫХ: Запрещено сокращать, резюмировать или выбрасывать части лекции. "
                "Весь теоретический материал должен быть сохранен.\n"
                "2. СТРУКТУРА: Используй иерархию заголовков (#, ##, ###), жирный шрифт для терминов и списки.\n"
                "3. КОД: Все примеры кода оформляй в соответствующие блоки (например, ```java).\n"
                "4. ТАБУ: Не добавляй от себя приветствия, заключения или комментарии ('Вот ваш текст', 'Надеюсь, это поможет').\n"
                "5. ЯЗЫК: Сохраняй оригинальный язык текста (русский)."
            )

            # ПОЛЬЗОВАТЕЛЬСКИЙ ПРОМТ: Только данные
            user_prompt = f"Преобразуй этот текст в Markdown, следуя системным правилам:\n\n{raw_text}"

            response: GenerateResponse = generate(
                model="qwen3:8b", 
                prompt=user_prompt,
                system=system_instruction,
                options={
                    "num_ctx": 20480,    
                    "temperature": 0.1,    
                    "num_predict": -1 
                }
            )

            return {
                "duration": response.total_duration,
                "answer": response.response
            }
        else:
            return {"error": "Текст PDF слишком длинный (более 50 000 символов)."}


cleaner = LectureCleaner()
file_name = "lec.pdf"
result = cleaner.process_pdf_to_md(file_name)
print(result["answer"])
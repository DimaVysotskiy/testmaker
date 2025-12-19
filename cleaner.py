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
        """Приватный метод: просто достает текст из PDF"""
        doc = pymupdf.open(pdf_path)
        text = ""
        for page in doc:
            text += "".join(page.get_text()) + "\n"
        return text

    def process_pdf_to_md(self, pdf_path):
        """Основной метод: PDF -> Markdown через LLM"""
        raw_text = self._extract_raw_text(pdf_path)
        
        if len(raw_text) <= 50000:
            prompt = (
            f"Преобразуй следующий текст лекции в чистый и хорошо структурированный формат Markdown. "
            f"Используй правильные заголовки (h1, h2, h3), маркированные списки и блоки кода там, где это уместно. "
            f"Обязательно: Не пишите введения или заключения, просто отформатируйте предоставленный текст. "
            f"ОБЯЗАТЕЛЬНО: Сохраняй язык оригинала (русский). Не переводи текст, не сокращай его и не добавляй ничего от себя. "
            f"Верни только структурированный текст лекции.\n\n"
            f"{raw_text}"
        )
            response: GenerateResponse = generate(
                model="qwen3:8b",
                prompt=prompt,
                options={
                    # Load time options (влияют на скорость загрузки и память)
                    "num_ctx": 16384,     # Увеличиваем контекст для длинных лекций
                    "num_thread": 8,      # Используем больше потоков CPU
                    
                    # Runtime options (влияют на саму генерацию)
                    "temperature": 0.1,   # Низкая температура = выше точность и скорость
                    "top_p": 0.9,
                    "num_predict": -1,    # -1 позволяет модели генерировать до конца
                    "repeat_penalty": 1.1 # Чтобы модель не зацикливалась на одном слове
                },
                system=""
            )

            result = {
                "Полное время выполнения запроса.": response.total_duration,
                "answer": response.response
            }

            return result
        else:
            return {"error": "PDF text exceeds the 50,000 character limit."}
        
cleaner = LectureCleaner()
print(cleaner.process_pdf_to_md("Лекция_5.pdf"))
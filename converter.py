import pymupdf 
import os
from dotenv import load_dotenv
from ollama import generate, Client
from ollama import GenerateResponse
import puremagic
from typing import List, Dict, Union



load_dotenv()



class ConverterToMd:
    """Конвертатор файлов лекций в md файлы. """
    def __init__(self):
        self.client = Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + str(os.environ.get('OLLAMA_API_KEY'))}
        )
        self.model = str(os.environ.get('LLM_MODEL'))


    def extract_pdf_raw_text(self, file_path: str) -> str:
        """Извлечение сырого текста из файла лекции в pdf формате."""
        try:
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += "".join(page.get_text()) + "\n"
            return text
        except Exception as e:
            raise RuntimeError(f"Ошибка при чтении PDF: {e}")
    

    def extract_docx_raw_text(self, file_path: str):
        """Извлечение сырого текста из файла лекции в docx формате."""
        pass


    def process_text_to_md(self, raw_text: str) -> str:
        """Преобразование текста в Markdown через LLM."""
        
        if len(raw_text) <= 50000:
            system_instruction = (
                "Ты — профессиональный редактор технических текстов и конспектов. "
                "Твоя задача: преобразовать сырой текст из PDF или Word в идеально структурированный Markdown. "
                "\n\nПРАВИЛА:\n"
                "1. СОХРАННОСТЬ ДАННЫХ: Запрещено сокращать, резюмировать или выбрасывать части лекции. "
                "Весь теоретический материал должен быть сохранен.\n"
                "2. СТРУКТУРА: Используй иерархию заголовков (#, ##, ###), жирный шрифт для терминов и списки.\n"
                "3. КОД: Все примеры кода оформляй в соответствующие блоки (например, ```java).\n"
                "4. ТАБУ: Не добавляй от себя приветствия, заключения или комментарии.\n"
                "5. ЯЗЫК: Сохраняй оригинальный язык текста (русский)."
            )

            user_prompt = f"Преобразуй этот текст в Markdown, следуя системным правилам:\n\n{raw_text}"

            response: GenerateResponse = self.client.generate(
                model=self.model, 
                prompt=user_prompt,
                system=system_instruction,
                options={"temperature": 0.1}
            )

            return response.response
        else:
            raise RuntimeError("Пока что я могу обрабатывать только тексты до 50 000 символов :(")
    

    def convert(self, file_path: str):
        """Главный метод конвертации файла лекции в md формат."""
        handlers = {
            ".pdf": self.extract_pdf_raw_text,
            ".docx": self.extract_docx_raw_text
        }

        ext_info = puremagic.from_file(file_path).lower()

        for ext, handler_func in handlers.items():
            if ext in ext_info:
                raw_text = handler_func(file_path)
                return self.process_text_to_md(raw_text)

        raise ValueError(f"Тип файла {ext_info} не поддерживается")
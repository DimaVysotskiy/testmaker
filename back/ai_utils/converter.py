from fastapi.responses import StreamingResponse
import pymupdf
import io
from ollama import Client, GenerateResponse
from fastapi import UploadFile, File, status, HTTPException
from docx import Document
from ..utils import settings




class ConverterToMd:
    """Конвертатор файлов лекций в md файлы."""
    def __init__(self):
        self.client = Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + settings.OLLAMA_API_KEY}
        )
        self.model = settings.LLM_MODEL


    def extract_pdf_raw_text(self, file_bytes: bytes) -> str:
        """Извлечение сырого текста из байтов PDF."""
        try:
            with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
                text = ""
                for page in doc:
                    text += page.get_text().__str__() + "\n"
                return text
        except Exception as e:
            raise RuntimeError(f"Ошибка при чтении PDF: {e}")


    def extract_docx_raw_text(self, file_bytes: bytes) -> str:
        """Извлечение сырого текста из байтов DOCX."""
        try:
            file_stream = io.BytesIO(file_bytes)
            doc = Document(file_stream)
            full_text = [para.text for para in doc.paragraphs]
            return "\n".join(full_text)
        except Exception as e:
            raise RuntimeError(f"Ошибка при чтении DOCX: {e}")


    def process_text_to_md(self, raw_text: str) -> str:
        """Преобразование текста в Markdown через LLM."""
        
        if not raw_text.strip():
            return "Не удалось извлечь текст из файла."

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
    

    async def convert_as_md_file(self, file: UploadFile = File(...)):
        """Главный метод конвертации файла лекции в md формат."""
        
        filename = file.filename.lower() if file.filename else ""
        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый формат файла. Пожалуйста, загружайте файлы в формате PDF или DOCX."
            )
        
        MAX_SIZE = 16 * 1024 * 1024
        
        content = await file.read()
        
        if len(content) > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Размер файла превышает 16 МБ."
            )

        
        try:
            raw_text = ""
            if filename.endswith(".pdf"):
                raw_text = self.extract_pdf_raw_text(content)
            elif filename.endswith(".docx"):
                raw_text = self.extract_docx_raw_text(content)
            
            md_result = self.process_text_to_md(raw_text)
            
            file_stream = io.BytesIO(md_result.encode('utf-8'))


            return StreamingResponse(
                file_stream,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=\"{"lecture"}\""
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def convert_as_md_text(self, file: UploadFile = File(...)):
        """Главный метод конвертации файла лекции в md формат."""
        
        filename = file.filename.lower() if file.filename else ""
        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый формат файла. Пожалуйста, загружайте файлы в формате PDF или DOCX."
            )
        
        MAX_SIZE = 16 * 1024 * 1024
        
        content = await file.read()
        
        if len(content) > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Размер файла превышает 16 МБ."
            )

        
        try:
            raw_text = ""
            if filename.endswith(".pdf"):
                raw_text = self.extract_pdf_raw_text(content)
            elif filename.endswith(".docx"):
                raw_text = self.extract_docx_raw_text(content)
            
            md_text_of_lecture = self.process_text_to_md(raw_text)
            
            return md_text_of_lecture

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )



converter = ConverterToMd()
import pymupdf 
import os
from dotenv import load_dotenv
from ollama import generate, Client
from ollama import GenerateResponse
import json
from typing import List, Dict, Union

load_dotenv()

class TestMaker:
    def __init__(self):
        self.client = Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + str(os.environ.get('OLLAMA_API_KEY'))}
        )


    def extract_raw_text(self, pdf_path: str) -> Dict[str, Union[str, Dict]] | str:
        """Конвертатор файлов в текст. В дальнейшем переделать в отдельный класс с поддержкой разных форматов."""
        if not pdf_path.endswith('.pdf'):
            return {"message": "Sorry, but now I can only process PDF files :("}

        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            for page in doc:
                text += "".join(page.get_text()) + "\n"
            return text
        except Exception as e:
            return {"message": f"Error processing PDF: {str(e)}"}


    def process_text_to_md(self, text: str) -> Dict[str, Union[str, Dict]]:
        """"""
        
        if len(text) <= 50000:
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

            user_prompt = f"Преобразуй этот текст в Markdown, следуя системным правилам:\n\n{text}"

            response: GenerateResponse = self.client.generate(
                model="gpt-oss:20b-cloud", 
                prompt=user_prompt,
                system=system_instruction
            )

            return {
                "md_text": response.response
            }
        else:
            return {"message": "Пока что я могу обрабатывать только тексты до 50 000 символов :("}
    

    def make_test(self, md_text_of_lecture, level="medium", count=10, test_name="Новый тест"):
        """
        Генерация теста с учетом равного распределения сложных типов вопросов.
        """
        
        system_instruction = (
            "Ты — эксперт по составлению тестов. Твоя задача: создать тест в формате JSON по тексту лекции. "
            
            "Вот четкий план составления теста в формате json:\n"


            "СОХРАННОСТЬ ДАННЫХ:"
            " - Вопросы должны быть основаны исключительно на материале лекции.\n"
            " - Запрещено добавлять вопросы, не относящиеся к лекции.\n"
            " - Запрещено сокращать, резюмировать или выбрасывать части лекции.\n\n"


            "ТИПЫ ВОПРОСОВ (type):\n"
            " - single_choice: Вопрос с одним правильным ответом.\n"
            " - multiple_choice: Вопрос с несколькими правильными ответами.\n"
            " - open_ended: Вопрос с развернутым ответом (одно слово). \n\n"
            

            "ТРЕБОВАНИЯ К 'open_ended':\n"
            " - Вопрос формулируется как определение: 'Как называется механизм...?', 'Какой термин обозначает...?'\n"
            " - В тексте вопроса ЗАПРЕЩЕНО упоминать само слово-ответ.\n"
            " - Ответ (correct_answer) — только ОДНО СУЩЕСТВИТЕЛЬНОЕ в именительном падеже.\n"
            " - Верный ответ (correct_answer) должен обязательно содержаться в тексте лекции.\n"
            " - Лучше всего сотавлять 'open_ended' на явно выделенных терминов в лекции.\n\n"


            "ТРЕБОВАНИЯ К 'single_choice' и 'multiple_choice':\n"
            " - Верный ответ (correct_answer) должен обязательно содержаться в тексте лекции.\n"
            " - Варианты ответов (answer_options) должны быть правдоподобными и основанными на тексте лекции, но неверные варианты должны быть ложными."
            "Они должны противоречить вопросу и не отвечать на него. Их ты можешь придумать сам, соблюдая описанные в этом пункте условия.\n"
            " - Для 'single_choice' должен быть один правильный ответ, для 'multiple_choice' — от двух до всех имеющихся.\n\n"


            "СЛОЖНОСТЬ ВОПРОСОВ (level):\n"
            " - easy: 80% всех вопросов 'single_choice', остальные 20% 'open_ended'\n"
            " - medium: 40% всех вопросов 'single_choice', ещё 40% 'multiple_choice', остальные 20% 'open_ended'\n"
            " - hard: 50% всех вопросов 'single_choice', ещё 40% 'multiple_choice' в которых может быть от 4 до 6 вариантов ответа, остальные 10% 'open_ended'\n\n"
            
            
            "ОБЩИЕ ПРАВИЛА:\n"
            " - Если в лекции нет терминов, которые можно использовать для 'open_ended', то вопросы этого типа не создавай.\n"
            " - Если пользователь просит слишком много вопросов, а в лекции недостаточно материала, чтобы создать уникальные вопросы, создай столько уникальных вопросов, сколько возможно, соблюдая остальные правила.\n"
            " - Если не получается создать нужное количество вопросов определенного типа в соответствии с уровнем сложности, создай столько, сколько возможно, а оставшиеся замени на 'single_choice'.\n"
            " - Если ты хочешь составить вопрос на основе примера приведенного в лекции, переформулируй его так, чтобы он не был дословным повторением примера. И обязательно опиши его целиком, чтобы пользователь мог ответить на этот вопрос видя перед собой контекст.\n"
            " - Итогом должен быть JSON-файл с тестом, который можно использовать для автоматической проверки ответов. А не строка ```json.\n\n"

            "Что не нужно придумывать самому, а нужно брать из запроса пользователя:\n"
            " - Название теста (test_name)\n"
            " - Уровень сложности (level)\n"
            " - Общее количество вопросов (count)\n\n"

            "ПРИМЕР ТЕСТА JSON:\n"
            "{\n"
            "  \"test_name\": \"Название вашего теста\",\n"
            "  \"questions\": [\n"
            "    {\n"
            "      \"type\": \"single_choice\",\n"
            "      \"question\": \"Как называется столица Франции?\",\n"
            "      \"answer_options\": {\"a\": \"Лондон\", \"b\": \"Париж\", \"c\": \"Берлин\"},\n"
            "      \"correct_answer\": [\"b\"]\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"multiple_choice\",\n"
            "      \"question\": \"Выберите четные числа:\",\n"
            "      \"answer_options\": {\"a\": \"2\", \"b\": \"3\", \"c\": \"4\", \"d\": \"5\"},\n"
            "      \"correct_answer\": [\"a\", \"c\"]\n"
            "    },\n"
            "    {\n"
            "      \"type\": \"open_ended\",\n"
            "      \"question\": \"Как называется процесс превращения воды в пар?\",\n"
            "      \"answer_options\": null,\n"
            "      \"correct_answer\": \"Испарение\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Сгенерируй тест по лекции ниже.\n"
            f"ПАРАМЕТРЫ:\n"
            f"- Название теста: {test_name}\n"
            f"- Уровень сложности: {level}\n"
            f"- Общее количество вопросов: {count}\n\n"
            f"ТЕКСТ ЛЕКЦИИ:\n{md_text_of_lecture}"
        )

        
        response: GenerateResponse = self.client.generate(
            model="gpt-oss:20b-cloud", 
            prompt=user_prompt,
            system=system_instruction,
            format={
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "test_name": { "type": "string" },
                    "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                        "type": { "type": "string" },
                        "question": { "type": "string" },
                        "answer_options": { "type": "object" },
                        "correct_answer": { "type": "array", "items": { "type": "string" } }
                        },
                        "required": ["type", "question", "correct_answer"]
                    }
                    }
                },
                "required": ["test_name", "questions"]
                }
        )

        return response.response
    

testMaker = TestMaker()
text = testMaker.process_text_to_md("lec.pdf")
print(text)
test = testMaker.make_test(text.get("md_text"))
print(test)

data = json.loads(test)
# 2. Сохраняем в файл с красивыми отступами
with open("quiz.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
    
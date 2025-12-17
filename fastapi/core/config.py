from pydantic_settings import BaseSettings
from pathlib import Path

# Определяем путь к корню проекта (на два уровня выше от fastapi/core/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    #настройки под бд
    TEST_BD_URL: str
    MAIN_BD_URL: str

    #настройки под jwt
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = str(ENV_FILE)

settings = Settings()


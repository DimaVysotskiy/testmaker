from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path
import os




class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "postgres"  # Имя сервиса в docker-compose
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_SCHEMA: str = "public"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_RECYCLE: int = 3600
    DEBUG: bool = False
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
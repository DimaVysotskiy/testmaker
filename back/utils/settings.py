from pydantic_settings import BaseSettings





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
    
    OLLAMA_API_KEY: str
    LLM_MODEL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # MinIO настройки
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_NAME: str = "task-files"
    MINIO_SECURE: bool = False  # True для HTTPS

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
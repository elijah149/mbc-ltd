"""
Application configuration, loaded from environment variables (.env).
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # General
    PROJECT_NAME: str = "MBCU LTD Management System"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "mbcu_user"
    POSTGRES_PASSWORD: str = "mbcu_password"
    POSTGRES_DB: str = "mbcu_erp"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v, info):
        if isinstance(v, str) and v:
            return v
        data = info.data
        return (
            f"postgresql+psycopg2://{data.get('POSTGRES_USER')}:"
            f"{data.get('POSTGRES_PASSWORD')}@{data.get('POSTGRES_SERVER')}:"
            f"{data.get('POSTGRES_PORT')}/{data.get('POSTGRES_DB')}"
        )

    # Redis / Celery
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_broker(cls, v, info):
        if isinstance(v, str) and v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/0"

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_backend(cls, v, info):
        if isinstance(v, str) and v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/1"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # File storage (MinIO / S3 compatible)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "mbcu-documents"
    MINIO_SECURE: bool = False

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # First superuser (bootstrap)
    FIRST_SUPERUSER_EMAIL: str = "admin@mbcu.co.tz"
    FIRST_SUPERUSER_PASSWORD: str = "ChangeMe123!"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

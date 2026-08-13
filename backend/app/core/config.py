"""
Core configuration module.
Uses Pydantic Settings for environment variable management with validation.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # ===== Application =====
    APP_NAME: str = "GovScheme AI"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Driven Multilingual Government Scheme Discovery & Eligibility System"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ===== Server =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # ===== Database =====
    DATABASE_URL: str = "sqlite+aiosqlite:///./govscheme.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # ===== Redis =====
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # ===== JWT Authentication =====
    JWT_SECRET_KEY: str = "a9f8d7c6b5e4a3f2d1c0b9e8a7f6d5c4b3a2e1f0d9c8b7a6f5e4d3c2b1a0f9"
    JWT_REFRESH_SECRET_KEY: str = "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ===== Email / SMTP =====
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@govscheme.ai"
    SMTP_FROM_NAME: str = "GovScheme AI"
    SMTP_USE_TLS: bool = True
    EMAIL_VERIFICATION_ENABLED: bool = False

    # ===== SMS (Twilio / MSG91) =====
    SMS_PROVIDER: str = "twilio"  # twilio | msg91
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = ""

    # ===== Google Translate API =====
    GOOGLE_TRANSLATE_API_KEY: str = ""
    TRANSLATION_CACHE_TTL: int = 86400  # 24 hours

    # ===== OpenAI (for RAG chatbot) =====
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # ===== ML Models =====
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    EMBEDDING_DIMENSION: int = 384

    # ===== Rate Limiting =====
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000

    # ===== File Upload =====
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_FILE_TYPES: str = "pdf,jpg,jpeg,png,doc,docx"

    # ===== Encryption =====
    AES_ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef"  # 32 bytes for AES-256

    # ===== Paths =====
    CSV_DATA_PATH: str = "./updated_data.csv"
    VECTOR_STORE_PATH: str = "./data/vector_store"
    LOG_DIR: str = "./logs"

    # ===== Frontend URL =====
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_file_types_list(self) -> list[str]:
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "CRM Kuroda Inteligente"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    # Fallback to local PostgreSQL if not specified
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/crm_kuroda"
    
    # JWT Authentication
    SECRET_KEY: str = "SUPER_SECRET_JWT_SIGNING_KEY_CHANGE_THIS_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    # Meta / WhatsApp Integration API (Desactivado temporalmente, usando enlaces manuales)
    # META_WHATSAPP_TOKEN: str = ""
    # META_PHONE_NUMBER_ID: str = ""
    # WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "kuroda_verify_token"
    
    # OpenRouter LLM API Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini" # Modelo rápido y confiable por defecto
    
    # Allow loading from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

"""
MediBot AI — Core Configuration
Reads from environment variables / .env file
"""
from dotenv import load_dotenv
import pathlib as _pl
load_dotenv(_pl.Path(__file__).parent.parent / ".env", override=True)

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MediBot AI"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-secret-key-in-production"

    # AI APIs (set at least one)
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Active AI provider: "openai" | "gemini" | "groq" | "fallback"
    AI_PROVIDER: str = "gemini"
    AI_MODEL: str = "gemini-1.5-flash"

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "medibot"

    # JWT
    JWT_SECRET: str = "jwt-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "*"]

    # OCR
    TESSERACT_CMD: str = "/usr/bin/tesseract"

    # RAG
    VECTOR_DB_PATH: str = "./data/vectorstore"
    MEDICAL_DOCS_PATH: str = "./data/medical_docs"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

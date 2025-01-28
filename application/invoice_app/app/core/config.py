from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Invoice Generator"
    DATABASE_URL: str = "sqlite+aiosqlite:///./invoice.db"
    STATIC_DIR: Path = Path("static")
    TEMPLATES_DIR: Path = Path("templates")
    SECRET_KEY: str = "your-secret-key-here"  # In production, use environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True

settings = Settings()
"""
Application configuration and settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    PROJECT_NAME: str = "VerTac"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./vertac.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Data Processing
    MAX_UPLOAD_SIZE_MB: int = 100
    SUPPORTED_FILE_FORMATS: str = "csv,xlsx,parquet"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

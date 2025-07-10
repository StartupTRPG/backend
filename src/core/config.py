from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 애플리케이션 기본 설정
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = False
    
    # MongoDB 설정
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    
    # Google OAuth2 설정
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 설정
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings() 
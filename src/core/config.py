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
    
    # JWT 설정 (Unity 클라이언트용)
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일 (Unity 게임용)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30일
    
    # Unity 클라이언트 설정
    UNITY_CLIENT_ID: str = "unity_client"
    UNITY_CLIENT_SECRET: str = "unity_secret_key"
    
    # CORS 설정 (Unity WebGL용)
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # Unity WebGL
        "http://127.0.0.1:8080"   # Unity WebGL
    ]
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings() 
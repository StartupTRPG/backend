from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 애플리케이션 기본 설정
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = False
    
    # MongoDB 설정
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    
    # JWT 설정 (웹 클라이언트용)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1일 (웹용)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7일
    
    # 암호화 설정
    ENCRYPTION_KEY: str
    
    # 웹 클라이언트 설정
    WEB_CLIENT_ID: str
    WEB_CLIENT_SECRET: str
    
    # CORS 설정 (웹 클라이언트용)
    FRONTEND_URL: str 
    ALLOWED_ORIGINS: list[str]
    
    # 로깅 설정
    LOG_LEVEL: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 전역 설정 인스턴스
settings = Settings() 
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
import logging
import traceback
import time
import json

from src.core.mongodb import connect_to_mongo, close_mongo_connection, ping_database, get_collection
from src.core.config import settings
from src.modules.auth.router import router as auth_router
from src.modules.room.router import router as room_router
from src.modules.profile.router import router as profile_router
from src.modules.chat.router import router as chat_router
from src.core.socket import create_socketio_app

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG 레벨로 설정하여 모든 로그 출력
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시 실행
    logger.info("애플리케이션을 시작합니다...")
    try:
        await connect_to_mongo()
        logger.info("MongoDB 연결이 완료되었습니다.")
    except Exception as e:
        logger.error(f"MongoDB 연결 실패: {e}")
        raise
    
    yield
    
    # 종료 시 실행
    logger.info("애플리케이션을 종료합니다...")
    await close_mongo_connection()
    logger.info("MongoDB 연결이 종료되었습니다.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 모든 500 에러를 로깅"""
    logger.error(f"Unhandled exception occurred: {exc}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Exception traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러 - 4xx, 5xx 에러 로깅"""
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} error: {exc.detail}")
        logger.error(f"Request URL: {request.url}")
        logger.error(f"Request method: {request.method}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)
app.include_router(room_router)
app.include_router(profile_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    return {
        "message": "Backend API is running",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    db_status = await ping_database()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_status else "disconnected"
    }

socket_app = create_socketio_app(app)

if __name__ == "__main__":
    uvicorn.run(
        socket_app,  # Socket.IO가 통합된 앱 사용
        host="0.0.0.0",
        port=8000,
        log_level="debug",  # DEBUG 레벨로 설정
        access_log=True,
        use_colors=True
    )

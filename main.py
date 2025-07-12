from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
import uvicorn
import logging
import traceback
import time
import json
import sys

from src.core.mongodb import connect_to_mongo, close_mongo_connection, ping_database, get_collection
from src.core.config import settings
from src.modules.auth.router import router as auth_router
from src.modules.room.router import router as room_router
from src.modules.profile.router import router as profile_router
from src.modules.chat.router import router as chat_router
from src.modules.admin.router import router as admin_router
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
    
    # 백그라운드 태스크 시작
    import asyncio
    from src.core.session_manager import session_manager
    
    async def cleanup_sessions_task():
        """주기적으로 비활성 세션 정리"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                await session_manager.cleanup_inactive_sessions()
            except Exception as e:
                logger.error(f"Session cleanup task error: {str(e)}")
    
    cleanup_task = asyncio.create_task(cleanup_sessions_task())
    
    yield
    
    # 종료 시 실행
    logger.info("애플리케이션을 종료합니다...")
    cleanup_task.cancel()
    await close_mongo_connection()
    logger.info("MongoDB 연결이 종료되었습니다.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    # 상세한 에러 정보 제공
    openapi_url="/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러 - 모든 예외를 상세히 로깅"""
    logger.error("=" * 80)
    logger.error("GLOBAL EXCEPTION HANDLER")
    logger.error("=" * 80)
    logger.error(f"Exception Type: {type(exc).__name__}")
    logger.error(f"Exception Message: {str(exc)}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request Method: {request.method}")
    logger.error(f"Request Headers: {dict(request.headers)}")
    
    # 요청 본문 로깅 (가능한 경우)
    try:
        body = await request.body()
        if body:
            # 바이트를 문자열로 변환하여 로깅
            body_str = body.decode('utf-8', errors='replace')
            logger.error(f"Request Body: {body_str}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")
    
    # 상세한 traceback 로깅
    logger.error("Full Traceback:")
    logger.error(traceback.format_exc())
    logger.error("=" * 80)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 데이터 검증 실패 핸들러 - 422 에러 상세 로깅"""
    logger.error("=" * 80)
    logger.error("422 VALIDATION ERROR HANDLER")
    logger.error("=" * 80)
    logger.error(f"Status Code: 422")
    logger.error(f"Error Type: RequestValidationError")
    logger.error(f"Validation Errors: {exc.errors()}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request Method: {request.method}")
    logger.error(f"Request Path: {request.url.path}")
    logger.error(f"Request Query: {dict(request.query_params)}")
    logger.error(f"Request Headers: {dict(request.headers)}")
    
    # 요청 본문 로깅 (가능한 경우)
    try:
        body = await request.body()
        if body:
            # 바이트를 문자열로 변환하여 로깅
            body_str = body.decode('utf-8', errors='replace')
            logger.error(f"Request Body: {body_str}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")
    
    # 상세한 traceback 로깅
    logger.error("Full Traceback:")
    logger.error(traceback.format_exc())
    logger.error("=" * 80)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "요청 데이터 검증에 실패했습니다.",
            "errors": exc.errors(),
            "status_code": 422,
            "error_type": "RequestValidationError",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러 - 모든 400 이상 에러 상세 로깅"""
    logger.error("=" * 80)
    logger.error(f"HTTP {exc.status_code} ERROR HANDLER")
    logger.error("=" * 80)
    logger.error(f"Status Code: {exc.status_code}")
    logger.error(f"Error Type: HTTPException")
    logger.error(f"Error Detail: {exc.detail}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request Method: {request.method}")
    logger.error(f"Request Path: {request.url.path}")
    logger.error(f"Request Query: {dict(request.query_params)}")
    logger.error(f"Request Headers: {dict(request.headers)}")
    
    # 요청 본문 로깅 (가능한 경우)
    try:
        body = await request.body()
        if body:
            # 바이트를 문자열로 변환하여 로깅
            body_str = body.decode('utf-8', errors='replace')
            logger.error(f"Request Body: {body_str}")
    except Exception as e:
        logger.error(f"Could not read request body: {e}")
    
    # 상세한 traceback 로깅
    logger.error("Full Traceback:")
    logger.error(traceback.format_exc())
    logger.error("=" * 80)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "error_type": "HTTPException",
            "timestamp": datetime.now().isoformat()
        }
    )

class ContentTypeMiddleware(BaseHTTPMiddleware):
    """Content-Type 헤더를 자동으로 수정하는 미들웨어"""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        # POST, PUT, PATCH 요청에서 Content-Type이 text/plain이지만 JSON 데이터인 경우 수정
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # text/plain으로 설정된 경우 JSON으로 변경
            if "text/plain" in content_type:
                # 요청 본문을 읽어서 JSON인지 확인
                try:
                    body = await request.body()
                    if body:
                        # JSON 파싱 시도
                        json_data = json.loads(body.decode('utf-8'))
                        
                        # JSON이면 Content-Type을 application/json으로 변경
                        request._headers = dict(request.headers)
                        request._headers["content-type"] = "application/json"
                        
                        # 요청 본문을 다시 설정 (중요!)
                        request._body = body
                        
                        logger.info(f"Content-Type 자동 수정: {content_type} -> application/json")
                        
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # JSON이 아니면 그대로 유지
                    pass
        
        response = await call_next(request)
        return response

# 미들웨어 등록 (순서 중요: CORS -> ContentType -> 라우터)
app.add_middleware(ContentTypeMiddleware)

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
app.include_router(admin_router)

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

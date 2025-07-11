from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
import logging

from src.core.mongodb import connect_to_mongo, close_mongo_connection, ping_database, get_collection
from src.core.config import settings
from src.core.jwt_utils import jwt_manager

from src.modules.auth.router import router as auth_router
from src.modules.room.router import router as room_router
from src.modules.user.profile_router import router as profile_router
from src.modules.chat.router import router as chat_router
from src.core.socket import create_socketio_app, get_socket_events_documentation
from src.core.swagger import custom_openapi

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    description="""
## 🎮 Madcamp Backend API

이 API는 게임 로비 및 실시간 채팅 기능을 제공합니다.

### 🔌 Socket.IO 연결
- **URL**: `ws://localhost:8000/socket.io/`
- **인증**: JWT 토큰 필요
- **연결 예시**:
```javascript
const socket = io('ws://localhost:8000', {
    auth: {
        token: 'your-jwt-token'
    }
});
```

### 🔐 인증
1. `/auth/login` 또는 `/auth/register`로 JWT 토큰 획득
2. REST API: `Authorization: Bearer <token>` 헤더 사용
3. Socket.IO: 연결 시 `auth.token`에 토큰 포함

### 📊 주요 기능
- **사용자 인증**: 회원가입, 로그인, 프로필 관리
- **방 관리**: 방 생성, 입장, 나가기
- **실시간 채팅**: 방별 채팅, 메시지 암호화
- **Socket.IO 이벤트**: 실시간 통신
    """
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

@app.get("/socket-docs", tags=["Documentation"])
async def get_socket_documentation():
    """Socket.IO 이벤트 문서"""
    return get_socket_events_documentation()

# 커스텀 OpenAPI 스키마 적용
app.openapi = lambda: custom_openapi(app)

# Socket.IO 앱 생성
socket_app = create_socketio_app(app)

if __name__ == "__main__":
    uvicorn.run(
        socket_app,  # Socket.IO가 통합된 앱 사용
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )

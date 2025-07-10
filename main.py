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

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
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
    lifespan=lifespan
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

@app.get("/test/mongodb")
async def test_mongodb():
    """MongoDB 연결 테스트 엔드포인트"""
    try:
        # 테스트 컬렉션 가져오기
        test_collection = get_collection("test")
        
        # 테스트 문서 삽입
        test_doc = {
            "message": "MongoDB 연결 테스트",
            "timestamp": datetime.now(),
            "test_id": "test_001"
        }
        
        result = await test_collection.insert_one(test_doc)
        
        # 삽입된 문서 조회
        inserted_doc = await test_collection.find_one({"_id": result.inserted_id})
        
        # ObjectId를 문자열로 변환
        inserted_doc["_id"] = str(inserted_doc["_id"])
        inserted_doc["timestamp"] = inserted_doc["timestamp"].isoformat()
        
        return {
            "status": "success",
            "message": "MongoDB 연결 및 작업이 성공적으로 완료되었습니다.",
            "inserted_document": inserted_doc
        }
        
    except Exception as e:
        logger.error(f"MongoDB 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"MongoDB 테스트 실패: {str(e)}")

@app.get("/test/mongodb/count")
async def test_mongodb_count():
    """MongoDB 컬렉션 문서 수 조회"""
    try:
        test_collection = get_collection("test")
        count = await test_collection.count_documents({})
        
        return {
            "status": "success",
            "collection": "test",
            "document_count": count
        }
        
    except Exception as e:
        logger.error(f"MongoDB 문서 수 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"MongoDB 문서 수 조회 실패: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )

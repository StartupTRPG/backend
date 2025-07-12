import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from src.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

class MongoManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect_to_mongo(self) -> None:
        """MongoDB Atlas에 연결"""
        try:
            logger.info("MongoDB 연결을 시도합니다...")
            
            # MongoDB 클라이언트 생성
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # 데이터베이스 선택
            self.database = self.client[settings.MONGODB_DB_NAME]
            
            # 연결 테스트
            await self.client.admin.command('ping')
            
            # 전역 변수에 할당
            MongoDB.client = self.client
            MongoDB.database = self.database
            
            logger.info(f"MongoDB 연결 성공: {settings.MONGODB_DB_NAME}")
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB 연결 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"MongoDB 연결 중 예상치 못한 오류: {e}")
            raise
    
    async def close_mongo_connection(self) -> None:
        """MongoDB 연결 종료"""
        try:
            if self.client:
                logger.info("MongoDB 연결을 종료합니다...")
                self.client.close()
                MongoDB.client = None
                MongoDB.database = None
                logger.info("MongoDB 연결이 종료되었습니다.")
        except Exception as e:
            logger.error(f"MongoDB 연결 종료 중 오류: {e}")
    
    async def ping_database(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"데이터베이스 ping 실패: {e}")
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """데이터베이스 인스턴스 반환"""
        if self.database is None:
            raise RuntimeError("데이터베이스가 연결되지 않았습니다. connect_to_mongo()를 먼저 호출하세요.")
        return self.database

    def get_collection(self, collection_name: str):
        """컬렉션 반환"""
        database = self.get_database()
        return database[collection_name]

# 전역 MongoDB 매니저 인스턴스
mongo_manager = MongoManager()

# 편의 함수들
async def connect_to_mongo() -> None:
    """MongoDB 연결"""
    await mongo_manager.connect_to_mongo()

async def close_mongo_connection() -> None:
    """MongoDB 연결 종료"""
    await mongo_manager.close_mongo_connection()

async def ping_database() -> bool:
    """데이터베이스 연결 상태 확인"""
    return await mongo_manager.ping_database()

def get_database() -> AsyncIOMotorDatabase:
    """데이터베이스 인스턴스 반환"""
    return mongo_manager.get_database()

def get_collection(collection_name: str):
    """컬렉션 반환"""
    return mongo_manager.get_collection(collection_name)

# 의존성 주입용 함수
async def get_mongo_client() -> AsyncIOMotorClient:
    """MongoDB 클라이언트 반환 (의존성 주입용)"""
    if MongoDB.client is None:
        raise RuntimeError("MongoDB 클라이언트가 연결되지 않았습니다.")
    return MongoDB.client

async def get_mongo_database() -> AsyncIOMotorDatabase:
    """MongoDB 데이터베이스 반환 (의존성 주입용)"""
    if MongoDB.database is None:
        raise RuntimeError("MongoDB 데이터베이스가 연결되지 않았습니다.")
    return MongoDB.database

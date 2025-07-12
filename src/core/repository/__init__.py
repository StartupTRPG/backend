from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

# 제네릭 타입 정의
T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Repository 기본 인터페이스"""
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """ID로 엔티티 조회"""
        pass
    
    @abstractmethod
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[T]:
        """조건으로 단일 엔티티 조회"""
        pass
    
    @abstractmethod
    async def find_many(self, filter_dict: Dict[str, Any], skip: int = 0, limit: int = 0) -> List[T]:
        """조건으로 여러 엔티티 조회"""
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> str:
        """엔티티 생성"""
        pass
    
    @abstractmethod
    async def update(self, id: str, update_dict: Dict[str, Any]) -> bool:
        """엔티티 업데이트"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """엔티티 삭제"""
        pass
    
    @abstractmethod
    async def count(self, filter_dict: Dict[str, Any]) -> int:
        """조건에 맞는 엔티티 개수 조회"""
        pass

class MongoRepository(BaseRepository[T]):
    """MongoDB Repository 구현체"""
    
    def __init__(self, collection_name: str, entity_class: type):
        self.collection_name = collection_name
        self.entity_class = entity_class
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    def _get_collection(self) -> AsyncIOMotorCollection:
        """컬렉션 지연 로딩"""
        if self._collection is None:
            from src.core.mongodb import get_collection
            self._collection = get_collection(self.collection_name)
        return self._collection
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """ID로 엔티티 조회"""
        try:
            collection = self._get_collection()
            doc = await collection.find_one({"_id": ObjectId(id)})
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return self.entity_class(**doc)
            return None
        except Exception as e:
            print(f"Error finding entity by id {id}: {e}")
            return None
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[T]:
        """조건으로 단일 엔티티 조회"""
        try:
            collection = self._get_collection()
            doc = await collection.find_one(filter_dict)
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return self.entity_class(**doc)
            return None
        except Exception as e:
            print(f"Error finding entity: {e}")
            return None
    
    async def find_many(self, filter_dict: Dict[str, Any], skip: int = 0, limit: int = 0) -> List[T]:
        """조건으로 여러 엔티티 조회"""
        try:
            collection = self._get_collection()
            cursor = collection.find(filter_dict).skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
            
            entities = []
            async for doc in cursor:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                entities.append(self.entity_class(**doc))
            
            return entities
        except Exception as e:
            print(f"Error finding entities: {e}")
            return []
    
    async def create(self, entity: T) -> str:
        """엔티티 생성"""
        try:
            collection = self._get_collection()
            entity_dict = entity.model_dump() if hasattr(entity, 'model_dump') else entity.__dict__
            
            # id 필드 제거 (MongoDB가 _id 자동 생성)
            entity_dict.pop("id", None)
            
            result = await collection.insert_one(entity_dict)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating entity: {e}")
            raise
    
    async def update(self, id: str, update_dict: Dict[str, Any]) -> bool:
        """엔티티 업데이트"""
        try:
            collection = self._get_collection()
            result = await collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_dict}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating entity {id}: {e}")
            return False
    
    async def delete(self, id: str) -> bool:
        """엔티티 삭제"""
        try:
            collection = self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting entity {id}: {e}")
            return False
    
    async def count(self, filter_dict: Dict[str, Any]) -> int:
        """조건에 맞는 엔티티 개수 조회"""
        try:
            collection = self._get_collection()
            return await collection.count_documents(filter_dict)
        except Exception as e:
            print(f"Error counting entities: {e}")
            return 0

# Repository Factory
class RepositoryFactory:
    """Repository 인스턴스 생성 팩토리"""
    
    _repositories: Dict[str, BaseRepository] = {}
    
    @classmethod
    def get_repository(cls, collection_name: str, entity_class: type) -> BaseRepository:
        """Repository 인스턴스 반환 (싱글톤 패턴)"""
        key = f"{collection_name}_{entity_class.__name__}"
        
        if key not in cls._repositories:
            cls._repositories[key] = MongoRepository(collection_name, entity_class)
        
        return cls._repositories[key]

# 편의 함수
def get_repository(collection_name: str, entity_class: type) -> BaseRepository:
    """Repository 인스턴스 반환"""
    return RepositoryFactory.get_repository(collection_name, entity_class) 
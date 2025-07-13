from abc import abstractmethod
from typing import Optional, List
from src.core.repository import BaseRepository
from .models import ChatMessage
from datetime import datetime

class ChatRepository(BaseRepository[ChatMessage]):
    """Chat Repository 인터페이스"""
    @abstractmethod
    async def find_by_room_id(self, room_id: str, skip: int = 0, limit: int = 0) -> List[ChatMessage]:
        pass

class MongoChatRepository(ChatRepository):
    def __init__(self):
        from src.core.repository import MongoRepository
        self._mongo_repo = MongoRepository("chat_messages", ChatMessage)
    async def find_by_id(self, id: str) -> Optional[ChatMessage]:
        # Apply soft delete: add is_deleted=False condition
        return await self._mongo_repo.find_one({"_id": id, "is_deleted": False})
    async def find_one(self, filter_dict):
        # Apply soft delete: add is_deleted=False condition
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        return await self._mongo_repo.find_one(filter_dict)
    async def find_many(self, filter_dict, skip: int = 0, limit: int = 0) -> List[ChatMessage]:
        # Apply soft delete: add is_deleted=False condition
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        messages = await self._mongo_repo.find_many(filter_dict, skip, limit)
        # profile_id가 없는 메시지는 제외
        return [msg for msg in messages if hasattr(msg, 'profile_id') and msg.profile_id]
    async def create(self, entity: ChatMessage) -> str:
        return await self._mongo_repo.create(entity)
    async def update(self, id: str, update_dict) -> bool:
        return await self._mongo_repo.update(id, update_dict)
    async def delete(self, id: str) -> bool:
        # Soft delete: update is_deleted, deleted_at instead of actual deletion
        return await self._mongo_repo.update(id, {"is_deleted": True, "deleted_at": datetime.utcnow()})
    async def count(self, filter_dict) -> int:
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        
        # room_id가 ObjectId일 수 있으므로 문자열로 변환하여 조회
        if "room_id" in filter_dict:
            from bson import ObjectId
            try:
                # ObjectId로 변환 시도
                object_id = ObjectId(filter_dict["room_id"])
                filter_dict["room_id"] = str(object_id)
            except:
                # 이미 문자열이면 그대로 사용
                pass
        
        return await self._mongo_repo.count(filter_dict)
    async def find_by_room_id(self, room_id: str, skip: int = 0, limit: int = 0) -> List[ChatMessage]:
        # Apply soft delete: add is_deleted=False condition
        # room_id가 ObjectId일 수 있으므로 문자열로 변환하여 조회
        from bson import ObjectId
        try:
            # ObjectId로 변환 시도
            object_id = ObjectId(room_id)
            messages = await self._mongo_repo.find_many({"room_id": str(object_id), "is_deleted": False}, skip, limit)
        except:
            # 문자열로 조회
            messages = await self._mongo_repo.find_many({"room_id": room_id, "is_deleted": False}, skip, limit)
        # profile_id가 없는 메시지는 제외
        return [msg for msg in messages if hasattr(msg, 'profile_id') and msg.profile_id]

class ChatRepositoryFactory:
    _instance: Optional[ChatRepository] = None
    @classmethod
    def get_repository(cls) -> ChatRepository:
        if cls._instance is None:
            cls._instance = MongoChatRepository()
        return cls._instance

def get_chat_repository() -> ChatRepository:
    return ChatRepositoryFactory.get_repository() 
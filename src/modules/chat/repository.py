from abc import ABC, abstractmethod
from typing import Optional, List
from src.core.repository import BaseRepository
from .models import ChatMessage

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
        return await self._mongo_repo.find_by_id(id)
    async def find_one(self, filter_dict):
        return await self._mongo_repo.find_one(filter_dict)
    async def find_many(self, filter_dict, skip: int = 0, limit: int = 0) -> List[ChatMessage]:
        return await self._mongo_repo.find_many(filter_dict, skip, limit)
    async def create(self, entity: ChatMessage) -> str:
        return await self._mongo_repo.create(entity)
    async def update(self, id: str, update_dict) -> bool:
        return await self._mongo_repo.update(id, update_dict)
    async def delete(self, id: str) -> bool:
        return await self._mongo_repo.delete(id)
    async def count(self, filter_dict) -> int:
        return await self._mongo_repo.count(filter_dict)
    async def find_by_room_id(self, room_id: str, skip: int = 0, limit: int = 0) -> List[ChatMessage]:
        return await self._mongo_repo.find_many({"room_id": room_id}, skip, limit)

class ChatRepositoryFactory:
    _instance: Optional[ChatRepository] = None
    @classmethod
    def get_repository(cls) -> ChatRepository:
        if cls._instance is None:
            cls._instance = MongoChatRepository()
        return cls._instance

def get_chat_repository() -> ChatRepository:
    return ChatRepositoryFactory.get_repository() 
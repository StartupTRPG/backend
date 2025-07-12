from abc import ABC, abstractmethod
from typing import Optional, List
from src.core.repository import BaseRepository
from .models import Room

class RoomRepository(BaseRepository[Room]):
    """Room Repository 인터페이스"""
    @abstractmethod
    async def find_by_title(self, title: str) -> Optional[Room]:
        pass
    @abstractmethod
    async def find_by_host_id(self, host_id: str) -> List[Room]:
        pass

class MongoRoomRepository(RoomRepository):
    def __init__(self):
        from src.core.repository import MongoRepository
        self._mongo_repo = MongoRepository("rooms", Room)
    async def find_by_id(self, id: str) -> Optional[Room]:
        return await self._mongo_repo.find_by_id(id)
    async def find_one(self, filter_dict):
        return await self._mongo_repo.find_one(filter_dict)
    async def find_many(self, filter_dict, skip: int = 0, limit: int = 0) -> List[Room]:
        return await self._mongo_repo.find_many(filter_dict, skip, limit)
    async def create(self, entity: Room) -> str:
        return await self._mongo_repo.create(entity)
    async def update(self, id: str, update_dict) -> bool:
        return await self._mongo_repo.update(id, update_dict)
    async def delete(self, id: str) -> bool:
        return await self._mongo_repo.delete(id)
    async def count(self, filter_dict) -> int:
        return await self._mongo_repo.count(filter_dict)
    async def find_by_title(self, title: str) -> Optional[Room]:
        return await self._mongo_repo.find_one({"title": title})
    async def find_by_host_id(self, host_id: str) -> List[Room]:
        return await self._mongo_repo.find_many({"host_id": host_id})

class RoomRepositoryFactory:
    _instance: Optional[RoomRepository] = None
    @classmethod
    def get_repository(cls) -> RoomRepository:
        if cls._instance is None:
            cls._instance = MongoRoomRepository()
        return cls._instance

def get_room_repository() -> RoomRepository:
    return RoomRepositoryFactory.get_repository() 
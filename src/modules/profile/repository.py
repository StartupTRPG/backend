from abc import ABC, abstractmethod
from typing import Optional, List
from src.core.repository import BaseRepository
from .models import UserProfileDocument

class ProfileRepository(BaseRepository[UserProfileDocument]):
    """Profile Repository 인터페이스"""
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[UserProfileDocument]:
        pass

class MongoProfileRepository(ProfileRepository):
    def __init__(self):
        from src.core.repository import MongoRepository
        self._mongo_repo = MongoRepository("user_profiles", UserProfileDocument)
    async def find_by_id(self, id: str) -> Optional[UserProfileDocument]:
        return await self._mongo_repo.find_by_id(id)
    async def find_one(self, filter_dict):
        return await self._mongo_repo.find_one(filter_dict)
    async def find_many(self, filter_dict, skip: int = 0, limit: int = 0) -> List[UserProfileDocument]:
        return await self._mongo_repo.find_many(filter_dict, skip, limit)
    async def create(self, entity: UserProfileDocument) -> str:
        return await self._mongo_repo.create(entity)
    async def update(self, id: str, update_dict) -> bool:
        return await self._mongo_repo.update(id, update_dict)
    async def delete(self, id: str) -> bool:
        return await self._mongo_repo.delete(id)
    async def count(self, filter_dict) -> int:
        return await self._mongo_repo.count(filter_dict)
    async def find_by_user_id(self, user_id: str) -> Optional[UserProfileDocument]:
        return await self._mongo_repo.find_one({"user_id": user_id})

class ProfileRepositoryFactory:
    _instance: Optional[ProfileRepository] = None
    @classmethod
    def get_repository(cls) -> ProfileRepository:
        if cls._instance is None:
            cls._instance = MongoProfileRepository()
        return cls._instance

def get_profile_repository() -> ProfileRepository:
    return ProfileRepositoryFactory.get_repository() 
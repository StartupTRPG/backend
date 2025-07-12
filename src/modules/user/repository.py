from abc import ABC, abstractmethod
from typing import Optional, List
from src.core.repository import BaseRepository
from .models import User, UserDocument
from .dto import UserResponse
from datetime import datetime

class UserRepository(BaseRepository[User]):
    """User Repository 인터페이스"""
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트"""
        pass
    
    @abstractmethod
    async def find_by_username_exclude_id(self, username: str, exclude_id: str) -> Optional[User]:
        """사용자명으로 사용자 조회 (특정 ID 제외)"""
        pass

class MongoUserRepository(UserRepository):
    """MongoDB User Repository 구현체"""
    
    def __init__(self):
        from src.core.repository import MongoRepository
        self._mongo_repo = MongoRepository("users", UserDocument)
    
    async def find_by_id(self, id: str) -> Optional[User]:
        from bson import ObjectId
        try:
            # 문자열 ID를 ObjectId로 변환
            object_id = ObjectId(id)
            user_doc = await self._mongo_repo.find_one({"_id": object_id, "is_deleted": False})
            if user_doc:
                return User(
                    id=user_doc.id,
                    username=user_doc.username,
                    email=user_doc.email,
                    nickname=user_doc.nickname,
                    password=user_doc.password,
                    salt=user_doc.salt,
                    created_at=user_doc.created_at,
                    updated_at=user_doc.updated_at,
                    last_login=user_doc.last_login,
                    is_deleted=getattr(user_doc, 'is_deleted', False),
                    deleted_at=getattr(user_doc, 'deleted_at', None)
                )
        except Exception as e:
            # ObjectId 변환 실패 시 None 반환
            print(f"Invalid ObjectId format: {id}, error: {e}")
        return None
    
    async def find_one(self, filter_dict):
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        user_doc = await self._mongo_repo.find_one(filter_dict)
        if user_doc:
            return User(
                id=user_doc.id,
                username=user_doc.username,
                email=user_doc.email,
                nickname=user_doc.nickname,
                password=user_doc.password,
                salt=user_doc.salt,
                created_at=user_doc.created_at,
                updated_at=user_doc.updated_at,
                last_login=user_doc.last_login,
                is_deleted=getattr(user_doc, 'is_deleted', False),
                deleted_at=getattr(user_doc, 'deleted_at', None)
            )
        return None
    
    async def find_many(self, filter_dict, skip: int = 0, limit: int = 0) -> List[User]:
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        user_docs = await self._mongo_repo.find_many(filter_dict, skip, limit)
        return [
            User(
                id=doc.id,
                username=doc.username,
                email=doc.email,
                nickname=doc.nickname,
                password=doc.password,
                salt=doc.salt,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                last_login=doc.last_login,
                is_deleted=getattr(doc, 'is_deleted', False),
                deleted_at=getattr(doc, 'deleted_at', None)
            ) for doc in user_docs
        ]
    
    async def create(self, entity: User) -> str:
        user_doc = UserDocument(
            username=entity.username,
            email=entity.email,
            nickname=entity.nickname,
            password=entity.password,
            salt=entity.salt,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            last_login=entity.last_login,
            is_deleted=getattr(entity, 'is_deleted', False),
            deleted_at=getattr(entity, 'deleted_at', None)
        )
        return await self._mongo_repo.create(user_doc)
    
    async def update(self, id: str, update_dict) -> bool:
        return await self._mongo_repo.update(id, update_dict)
    
    async def delete(self, id: str) -> bool:
        # soft delete: 실제 삭제 대신 is_deleted, deleted_at update
        return await self._mongo_repo.update(id, {"is_deleted": True, "deleted_at": datetime.utcnow()})
    
    async def count(self, filter_dict) -> int:
        filter_dict = dict(filter_dict)
        filter_dict["is_deleted"] = False
        return await self._mongo_repo.count(filter_dict)
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """사용자명으로 사용자 조회"""
        return await self.find_one({"username": username})
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return await self.find_one({"email": email})
    
    async def update_last_login(self, user_id: str) -> bool:
        """마지막 로그인 시간 업데이트"""
        try:
            return await self._mongo_repo.update(user_id, {"last_login": datetime.utcnow()})
        except Exception as e:
            print(f"Error updating last login for user {user_id}: {e}")
            return False
    
    async def find_by_username_exclude_id(self, username: str, exclude_id: str) -> Optional[User]:
        """사용자명으로 사용자 조회 (특정 ID 제외)"""
        from bson import ObjectId
        return await self.find_one({
            "username": username,
            "_id": {"$ne": ObjectId(exclude_id)}
        })

# Repository Factory
class UserRepositoryFactory:
    """User Repository 팩토리"""
    
    _instance: Optional[UserRepository] = None
    
    @classmethod
    def get_repository(cls) -> UserRepository:
        """User Repository 인스턴스 반환 (싱글톤 패턴)"""
        if cls._instance is None:
            cls._instance = MongoUserRepository()
        return cls._instance

# 편의 함수
def get_user_repository() -> UserRepository:
    """User Repository 인스턴스 반환"""
    return UserRepositoryFactory.get_repository() 
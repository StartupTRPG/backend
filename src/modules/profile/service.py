from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from src.core.mongodb import get_collection
from src.modules.user.dto.user_response import UserResponse
from .models import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse, 
    UserProfilePublicResponse
)

class UserProfileService:
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """사용자 프로필 컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("user_profiles")
        return self.collection
    
    async def create_profile(self, user: UserResponse, profile_data: UserProfileCreate) -> UserProfileResponse:
        """사용자 프로필 생성"""
        collection = self._get_collection()
        
        try:
            # 이미 프로필이 있는지 확인
            existing_profile = await collection.find_one({"user_id": user.id})
            if existing_profile:
                raise ValueError("이미 프로필이 존재합니다.")
            
            # 표시 이름 중복 확인
            display_name_exists = await collection.find_one({"display_name": profile_data.display_name})
            if display_name_exists:
                raise ValueError("이미 사용 중인 표시 이름입니다.")
            
            # 프로필 문서 생성
            profile_doc = {
                "user_id": user.id,
                "username": user.username,
                "display_name": profile_data.display_name,
                "bio": profile_data.bio,
                "avatar_url": profile_data.avatar_url,
                "user_level": profile_data.user_level,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(profile_doc)
            profile_doc["id"] = str(result.inserted_id)
            
            return UserProfileResponse(**profile_doc)
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"프로필 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        """사용자 프로필 조회"""
        collection = self._get_collection()
        
        try:
            profile_doc = await collection.find_one({"user_id": user_id})
            if not profile_doc:
                return None
            
            profile_doc["id"] = str(profile_doc["_id"])
            return UserProfileResponse(**profile_doc)
            
        except Exception:
            return None
    
    async def get_public_profile(self, user_id: str) -> Optional[UserProfilePublicResponse]:
        """공개 프로필 조회 (다른 사용자용)"""
        collection = self._get_collection()
        
        try:
            profile_doc = await collection.find_one({"user_id": user_id})
            if not profile_doc:
                return None
            
            return UserProfilePublicResponse(**profile_doc)
            
        except Exception:
            return None
    
    async def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfileResponse]:
        """사용자 프로필 업데이트"""
        collection = self._get_collection()
        
        try:
            # 프로필 존재 확인
            existing_profile = await collection.find_one({"user_id": user_id})
            if not existing_profile:
                raise ValueError("프로필을 찾을 수 없습니다.")
            
            # 표시 이름 중복 확인 (다른 사용자가 사용 중인지)
            if profile_data.display_name:
                display_name_exists = await collection.find_one({
                    "display_name": profile_data.display_name,
                    "user_id": {"$ne": user_id}
                })
                if display_name_exists:
                    raise ValueError("이미 사용 중인 표시 이름입니다.")
            
            # 업데이트할 필드 구성
            update_fields = {"updated_at": datetime.utcnow()}
            
            if profile_data.display_name is not None:
                update_fields["display_name"] = profile_data.display_name
            if profile_data.bio is not None:
                update_fields["bio"] = profile_data.bio
            if profile_data.avatar_url is not None:
                update_fields["avatar_url"] = profile_data.avatar_url
            if profile_data.user_level is not None:
                update_fields["user_level"] = profile_data.user_level
            
            # 프로필 업데이트
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": update_fields}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_profile(user_id)
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"프로필 업데이트 중 오류가 발생했습니다: {str(e)}")
    
    async def delete_profile(self, user_id: str) -> bool:
        """사용자 프로필 삭제"""
        collection = self._get_collection()
        
        try:
            # 프로필 삭제
            profile_result = await collection.delete_one({"user_id": user_id})
            return profile_result.deleted_count > 0
            
        except Exception:
            return False
    
    async def search_profiles(self, query: str, limit: int = 20) -> List[UserProfilePublicResponse]:
        """프로필 검색"""
        collection = self._get_collection()
        
        try:
            # 표시 이름 또는 사용자명으로 검색
            search_filter = {
                "$or": [
                    {"display_name": {"$regex": query, "$options": "i"}},
                    {"username": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = collection.find(search_filter).limit(limit)
            profiles_docs = await cursor.to_list(length=None)
            
            profiles = []
            for profile_doc in profiles_docs:
                profiles.append(UserProfilePublicResponse(**profile_doc))
            
            return profiles
            
        except Exception:
            return []

# 전역 서비스 인스턴스
user_profile_service = UserProfileService() 
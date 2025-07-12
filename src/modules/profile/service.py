from datetime import datetime
from typing import Optional, List
from src.modules.user.dto.user_response import UserResponse
from .models import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse, 
    UserProfilePublicResponse, UserProfileDocument
)
from .repository import get_profile_repository, ProfileRepository

class UserProfileService:
    def __init__(self, profile_repository: ProfileRepository = None):
        self.profile_repository = profile_repository or get_profile_repository()
    
    async def create_profile(self, user: UserResponse, profile_data: UserProfileCreate) -> UserProfileResponse:
        try:
            # 이미 프로필이 있는지 확인
            existing_profile = await self.profile_repository.find_by_user_id(user.id)
            if existing_profile:
                raise ValueError("이미 프로필이 존재합니다.")
            # 표시 이름 중복 확인
            display_name_exists = await self.profile_repository.find_one({"display_name": profile_data.display_name})
            if display_name_exists:
                raise ValueError("이미 사용 중인 표시 이름입니다.")
            # 프로필 엔티티 생성
            profile = UserProfileDocument(
                user_id=user.id,
                username=user.username,
                display_name=profile_data.display_name,
                bio=profile_data.bio,
                avatar_url=profile_data.avatar_url,
                user_level=profile_data.user_level,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            profile_id = await self.profile_repository.create(profile)
            return UserProfileResponse(
                id=profile_id,
                user_id=profile.user_id,
                username=profile.username,
                display_name=profile.display_name,
                bio=profile.bio,
                avatar_url=profile.avatar_url,
                user_level=profile.user_level,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"프로필 생성 중 오류가 발생했습니다: {str(e)}")
    
    async def get_profile(self, user_id: str) -> Optional[UserProfileResponse]:
        try:
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                return None
            return UserProfileResponse(
                id=getattr(profile, 'id', None),
                user_id=profile.user_id,
                username=profile.username,
                display_name=profile.display_name,
                bio=profile.bio,
                avatar_url=profile.avatar_url,
                user_level=profile.user_level,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
        except Exception:
            return None
    
    async def get_public_profile(self, user_id: str) -> Optional[UserProfilePublicResponse]:
        try:
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                return None
            return UserProfilePublicResponse(
                user_id=profile.user_id,
                username=profile.username,
                display_name=profile.display_name,
                bio=profile.bio,
                avatar_url=profile.avatar_url,
                user_level=profile.user_level,
                created_at=profile.created_at
            )
        except Exception:
            return None
    
    async def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfileResponse]:
        try:
            existing_profile = await self.profile_repository.find_by_user_id(user_id)
            if not existing_profile:
                raise ValueError("프로필을 찾을 수 없습니다.")
            if profile_data.display_name:
                display_name_exists = await self.profile_repository.find_one({
                    "display_name": profile_data.display_name,
                    "user_id": {"$ne": user_id}
                })
                if display_name_exists:
                    raise ValueError("이미 사용 중인 표시 이름입니다.")
            update_fields = {"updated_at": datetime.utcnow()}
            if profile_data.display_name is not None:
                update_fields["display_name"] = profile_data.display_name
            if profile_data.bio is not None:
                update_fields["bio"] = profile_data.bio
            if profile_data.avatar_url is not None:
                update_fields["avatar_url"] = profile_data.avatar_url
            if profile_data.user_level is not None:
                update_fields["user_level"] = profile_data.user_level
            success = await self.profile_repository.update(existing_profile.id, update_fields)
            if not success:
                return None
            return await self.get_profile(user_id)
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"프로필 업데이트 중 오류가 발생했습니다: {str(e)}")
    
    async def delete_profile(self, user_id: str) -> bool:
        try:
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                return False
            return await self.profile_repository.delete(profile.id)
        except Exception:
            return False
    
    async def search_profiles(self, query: str, limit: int = 20) -> List[UserProfilePublicResponse]:
        try:
            search_filter = {
                "$or": [
                    {"display_name": {"$regex": query, "$options": "i"}},
                    {"username": {"$regex": query, "$options": "i"}}
                ]
            }
            profiles = await self.profile_repository.find_many(search_filter, 0, limit)
            return [UserProfilePublicResponse(
                user_id=p.user_id,
                username=p.username,
                display_name=p.display_name,
                bio=p.bio,
                avatar_url=p.avatar_url,
                user_level=p.user_level,
                created_at=p.created_at
            ) for p in profiles]
        except Exception:
            return []

user_profile_service = UserProfileService() 
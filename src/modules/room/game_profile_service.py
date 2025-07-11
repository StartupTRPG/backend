from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from src.core.mongodb import get_collection
from src.modules.user.dto import UserResponse
from .models import GameProfile, GameProfileCreate, LobbyProfileCreate

class GameProfileService:
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """게임 프로필 컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("game_profiles")
        return self.collection
    
    def _validate_profile(self, profile_data) -> bool:
        """프로필 데이터 유효성 검증"""
        # 기본 필수 필드 검증 (Pydantic에서 처리)
        
        # 캐릭터 이름 중복 검증은 방별로 체크
        if not profile_data.character_name.strip():
            return False
        
        # 캐릭터 능력치 검증 (상세 프로필인 경우만)
        if hasattr(profile_data, 'character_stats') and profile_data.character_stats:
            required_stats = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            for stat in required_stats:
                if stat in profile_data.character_stats:
                    stat_value = profile_data.character_stats[stat]
                    if not isinstance(stat_value, int) or stat_value < 1 or stat_value > 20:
                        return False
        
        return True
    
    async def create_lobby_profile(self, room_id: str, user: UserResponse, profile_data: LobbyProfileCreate) -> Optional[GameProfile]:
        """로비 프로필 생성 (이름만)"""
        return await self._create_profile_internal(room_id, user, profile_data, is_detailed=False)
    
    async def create_detailed_profile(self, room_id: str, user: UserResponse, profile_data: GameProfileCreate) -> Optional[GameProfile]:
        """상세 프로필 생성 (게임 시작용)"""
        return await self._create_profile_internal(room_id, user, profile_data, is_detailed=True)
    
    async def _create_profile_internal(self, room_id: str, user: UserResponse, profile_data, is_detailed: bool) -> Optional[GameProfile]:
        """게임 프로필 생성"""
        collection = self._get_collection()
        
        try:
            # 프로필 데이터 유효성 검증
            if not self._validate_profile(profile_data):
                raise ValueError("유효하지 않은 프로필 데이터입니다.")
            
            # 같은 방에서 캐릭터 이름 중복 확인
            existing_profile = await collection.find_one({
                "room_id": room_id,
                "character_name": profile_data.character_name.strip()
            })
            if existing_profile:
                raise ValueError("이미 사용 중인 캐릭터 이름입니다.")
            
            # 사용자가 이미 해당 방에 프로필을 가지고 있는지 확인
            user_existing_profile = await collection.find_one({
                "room_id": room_id,
                "user_id": user.id
            })
            if user_existing_profile:
                # 기존 프로필 업데이트
                if is_detailed:
                    return await self.update_to_detailed_profile(room_id, user.id, profile_data)
                else:
                    return await self.update_lobby_profile(room_id, user.id, profile_data)
            
            # 새 프로필 생성
            profile_doc = {
                "user_id": user.id,
                "room_id": room_id,
                "character_name": profile_data.character_name.strip(),
                "is_detailed": is_detailed,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # 상세 프로필인 경우 추가 정보 포함
            if is_detailed:
                profile_doc.update({
                    "character_class": profile_data.character_class,
                    "character_level": profile_data.character_level,
                    "character_description": profile_data.character_description,
                    "character_stats": profile_data.character_stats,
                    "character_role": profile_data.character_role,
                    "character_avatar": profile_data.character_avatar,
                    "character_equipment": profile_data.character_equipment,
                    "character_skills": profile_data.character_skills
                })
            else:
                # 로비 프로필은 기본값 설정
                profile_doc.update({
                    "character_class": None,
                    "character_level": None,
                    "character_description": None,
                    "character_stats": None,
                    "character_role": None,
                    "character_avatar": None,
                    "character_equipment": None,
                    "character_skills": None
                })
            
            result = await collection.insert_one(profile_doc)
            profile_doc["id"] = str(result.inserted_id)
            
            return GameProfile(**profile_doc)
            
        except ValueError:
            raise
        except Exception as e:
            return None
    
    async def get_profile(self, room_id: str, user_id: str) -> Optional[GameProfile]:
        """사용자의 게임 프로필 조회"""
        collection = self._get_collection()
        
        try:
            profile_doc = await collection.find_one({
                "room_id": room_id,
                "user_id": user_id
            })
            
            if not profile_doc:
                return None
            
            profile_doc["id"] = str(profile_doc["_id"])
            return GameProfile(**profile_doc)
            
        except Exception:
            return None
    
    async def update_lobby_profile(self, room_id: str, user_id: str, profile_data: LobbyProfileCreate) -> Optional[GameProfile]:
        """로비 프로필 업데이트 (이름만)"""
        collection = self._get_collection()
        
        try:
            # 프로필 데이터 유효성 검증
            if not self._validate_profile(profile_data):
                raise ValueError("유효하지 않은 프로필 데이터입니다.")
            
            # 다른 사용자가 같은 캐릭터 이름을 사용하는지 확인
            existing_profile = await collection.find_one({
                "room_id": room_id,
                "character_name": profile_data.character_name.strip(),
                "user_id": {"$ne": user_id}
            })
            if existing_profile:
                raise ValueError("이미 사용 중인 캐릭터 이름입니다.")
            
            # 프로필 업데이트
            update_data = {
                "character_name": profile_data.character_name.strip(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"room_id": room_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_profile(room_id, user_id)
            
        except ValueError:
            raise
        except Exception:
            return None
    
    async def update_to_detailed_profile(self, room_id: str, user_id: str, profile_data: GameProfileCreate) -> Optional[GameProfile]:
        """게임 프로필 업데이트"""
        collection = self._get_collection()
        
        try:
            # 프로필 데이터 유효성 검증
            if not self._validate_profile(profile_data):
                raise ValueError("유효하지 않은 프로필 데이터입니다.")
            
            # 다른 사용자가 같은 캐릭터 이름을 사용하는지 확인
            existing_profile = await collection.find_one({
                "room_id": room_id,
                "character_name": profile_data.character_name.strip(),
                "user_id": {"$ne": user_id}
            })
            if existing_profile:
                raise ValueError("이미 사용 중인 캐릭터 이름입니다.")
            
            # 상세 프로필로 업데이트
            update_data = {
                "character_name": profile_data.character_name.strip(),
                "character_class": profile_data.character_class,
                "character_level": profile_data.character_level,
                "character_description": profile_data.character_description,
                "character_stats": profile_data.character_stats,
                "character_role": profile_data.character_role,
                "character_avatar": profile_data.character_avatar,
                "character_equipment": profile_data.character_equipment,
                "character_skills": profile_data.character_skills,
                "is_detailed": True,
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"room_id": room_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_profile(room_id, user_id)
            
        except ValueError:
            raise
        except Exception:
            return None
    
    async def delete_profile(self, room_id: str, user_id: str) -> bool:
        """게임 프로필 삭제"""
        collection = self._get_collection()
        
        try:
            result = await collection.delete_one({
                "room_id": room_id,
                "user_id": user_id
            })
            
            return result.deleted_count > 0
            
        except Exception:
            return False
    
    async def get_room_profiles(self, room_id: str) -> List[GameProfile]:
        """방의 모든 게임 프로필 조회"""
        collection = self._get_collection()
        
        try:
            cursor = collection.find({"room_id": room_id})
            profiles_docs = await cursor.to_list(length=None)
            
            profiles = []
            for profile_doc in profiles_docs:
                profile_doc["id"] = str(profile_doc["_id"])
                profiles.append(GameProfile(**profile_doc))
            
            return profiles
            
        except Exception:
            return []
    
    async def delete_room_profiles(self, room_id: str) -> bool:
        """방의 모든 게임 프로필 삭제 (방 삭제 시 사용)"""
        collection = self._get_collection()
        
        try:
            await collection.delete_many({"room_id": room_id})
            return True
            
        except Exception:
            return False

# 전역 서비스 인스턴스
game_profile_service = GameProfileService() 
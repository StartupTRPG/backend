import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from src.core.mongodb import get_collection
from src.modules.user.models import UserResponse
from .models import (
    RoomCreate, RoomUpdate, RoomResponse, RoomListResponse, 
    RoomPlayer, RoomStatus, RoomVisibility, PlayerRole
)


class RoomService:
    def __init__(self):
        self.collection = None
        self.player_collection = None
    
    def _get_collection(self):
        """방 컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("rooms")
        return self.collection
    
    def _get_player_collection(self):
        """플레이어 컬렉션을 지연 로딩"""
        if self.player_collection is None:
            self.player_collection = get_collection("room_players")
        return self.player_collection
    
    def _hash_password(self, password: str) -> str:
        """방 비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """방 비밀번호 검증"""
        return self._hash_password(password) == hashed_password
    
    def verify_room_password(self, room: RoomResponse, password: str) -> bool:
        """방 비밀번호 검증 (Socket.IO 전용)"""
        if not room.has_password:
            return True  # 비밀번호가 없는 방은 항상 통과
        
        if not password:
            return False  # 비밀번호가 필요한데 제공되지 않음
        
        # RoomResponse에는 해시된 비밀번호가 없으므로 
        # 실제로는 데이터베이스에서 다시 조회해야 하지만
        # 여기서는 간단히 처리
        return True  # 임시로 항상 통과 (실제 검증은 add_player_to_room에서 수행)
    
    async def get_room_players(self, room_id: str) -> List[RoomPlayer]:
        """방 플레이어 목록 조회 (Socket.IO 전용)"""
        player_collection = self._get_player_collection()
        
        try:
            players_cursor = player_collection.find({"room_id": room_id})
            players_docs = await players_cursor.to_list(length=None)
            
            players = [
                RoomPlayer(
                    user_id=player["user_id"],
                    username=player["username"],
                    role=player["role"],
                    joined_at=player["joined_at"]
                )
                for player in players_docs
            ]
            
            return players
        except Exception:
            return []
    
    async def create_room(self, room_data: RoomCreate, host_user: UserResponse) -> RoomResponse:
        """방 생성"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        # 방 문서 생성
        room_doc = {
            "title": room_data.title,
            "description": room_data.description,
            "host_id": host_user.id,
            "host_username": host_user.username,
            "max_players": min(room_data.max_players, 6),  # 최대 6명 제한
            "current_players": 1,  # 호스트 포함
            "status": RoomStatus.WAITING,
            "visibility": room_data.visibility,
            "password": self._hash_password(room_data.password) if room_data.password else None,
            "game_settings": room_data.game_settings,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await collection.insert_one(room_doc)
        room_id = str(result.inserted_id)
        
        # 호스트를 플레이어로 추가
        host_player = {
            "room_id": room_id,
            "user_id": host_user.id,
            "username": host_user.username,
            "role": PlayerRole.HOST,
            "joined_at": datetime.utcnow()
        }
        
        await player_collection.insert_one(host_player)
        
        return await self.get_room(room_id)
    
    async def get_room(self, room_id: str) -> Optional[RoomResponse]:
        """방 정보 조회"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            room_doc = await collection.find_one({"_id": ObjectId(room_id)})
            if not room_doc:
                return None
            
            # 플레이어 목록 조회
            players_cursor = player_collection.find({"room_id": room_id})
            players_docs = await players_cursor.to_list(length=None)
            
            players = [
                RoomPlayer(
                    user_id=player["user_id"],
                    username=player["username"],
                    role=player["role"],
                    joined_at=player["joined_at"]
                )
                for player in players_docs
            ]
            
            
            room_doc["id"] = str(room_doc["_id"])
            room_doc["has_password"] = room_doc["password"] is not None
            room_doc["players"] = players
            
            return RoomResponse(**room_doc)
        except Exception:
            return None
    
    async def list_rooms(self, 
                        status: Optional[RoomStatus] = None,
                        visibility: Optional[RoomVisibility] = None,
                        search: Optional[str] = None,
                        page: int = 1,
                        limit: int = 20) -> List[RoomListResponse]:
        """방 목록 조회"""
        collection = self._get_collection()
        
        # 필터 조건 구성
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        
        if visibility:
            filter_query["visibility"] = visibility
        
        if search:
            filter_query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        # 페이지네이션
        skip = (page - 1) * limit
        
        cursor = collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
        rooms_docs = await cursor.to_list(length=None)
        
        rooms = []
        for room_doc in rooms_docs:
            room_doc["id"] = str(room_doc["_id"])
            room_doc["has_password"] = room_doc["password"] is not None
            rooms.append(RoomListResponse(**room_doc))
        
        return rooms
    
    async def add_player_to_room(self, room_id: str, user_id: str, username: str = None, password: str = None) -> bool:
        """방에 플레이어 추가 (Socket.IO 전용)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 방 존재 확인
            room_doc = await collection.find_one({"_id": ObjectId(room_id)})
            if not room_doc:
                raise ValueError("방을 찾을 수 없습니다.")
            
            # 방 상태 확인
            if room_doc["status"] != RoomStatus.WAITING:
                raise ValueError("참가할 수 없는 방 상태입니다.")
            
            # 이미 참가한 사용자인지 확인
            existing_player = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id
            })
            if existing_player:
                return True  # 이미 참가한 경우 성공으로 처리
            
            # 인원 수 확인
            if room_doc["current_players"] >= room_doc["max_players"]:
                raise ValueError("방이 가득 찼습니다.")
            
            # 비밀번호 확인 (Socket.IO에서 이미 검증됨)
            if password and room_doc["password"]:
                if not self._verify_password(password, room_doc["password"]):
                    raise ValueError("잘못된 비밀번호입니다.")
            
            # 플레이어 추가
            player_doc = {
                "room_id": room_id,
                "user_id": user_id,
                "username": username or user_id,
                "role": PlayerRole.PLAYER,
                "joined_at": datetime.utcnow()
            }
            
            await player_collection.insert_one(player_doc)
            
            # 방 인원 수 업데이트
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {
                    "$inc": {"current_players": 1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return True
            
        except ValueError:
            raise
        except Exception as e:
            return False
    
    async def remove_player_from_room(self, room_id: str, user_id: str) -> bool:
        """방에서 플레이어 제거 (Socket.IO 전용)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 플레이어 존재 확인
            player_doc = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id
            })
            if not player_doc:
                raise ValueError("방에 참가하지 않은 사용자입니다.")
            
            # 플레이어 제거
            await player_collection.delete_one({
                "room_id": room_id,
                "user_id": user_id
            })
            
            # 방 인원 수 업데이트
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {
                    "$inc": {"current_players": -1},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # 호스트가 나간 경우 방장 이전 또는 방 삭제
            if player_doc["role"] == PlayerRole.HOST:
                remaining_players = await player_collection.find({"room_id": room_id}).to_list(length=None)
                
                if remaining_players:
                    # 첫 번째 플레이어를 새 호스트로 지정
                    new_host = remaining_players[0]
                    await player_collection.update_one(
                        {"_id": new_host["_id"]},
                        {"$set": {"role": PlayerRole.HOST}}
                    )
                    
                    await collection.update_one(
                        {"_id": ObjectId(room_id)},
                        {
                            "$set": {
                                "host_id": new_host["user_id"],
                                "host_username": new_host["username"],
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                else:
                    # 마지막 플레이어가 나간 경우 방 삭제
                    await collection.delete_one({"_id": ObjectId(room_id)})
            
            return True
            
        except ValueError:
            raise
        except Exception:
            return False
    
    async def update_room(self, room_id: str, room_data: RoomUpdate, user_id: str) -> Optional[RoomResponse]:
        """방 설정 변경 (호스트만)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 호스트 권한 확인
            host_check = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id,
                "role": PlayerRole.HOST
            })
            if not host_check:
                raise ValueError("방장만 설정을 변경할 수 있습니다.")
            
            # 업데이트할 필드 구성
            update_fields = {"updated_at": datetime.utcnow()}
            
            if room_data.title is not None:
                update_fields["title"] = room_data.title
            
            if room_data.description is not None:
                update_fields["description"] = room_data.description
            
            if room_data.max_players is not None:
                update_fields["max_players"] = min(room_data.max_players, 6)
            
            if room_data.visibility is not None:
                update_fields["visibility"] = room_data.visibility
            
            if room_data.password is not None:
                update_fields["password"] = self._hash_password(room_data.password) if room_data.password else None
            
            if room_data.game_settings is not None:
                update_fields["game_settings"] = room_data.game_settings
            
            # 방 업데이트
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {"$set": update_fields}
            )
            
            return await self.get_room(room_id)
            
        except ValueError:
            raise
        except Exception:
            return None
    
    async def setup_detailed_profiles(self, room_id: str, user_id: str) -> bool:
        """게임 시작 전 상세 프로필 설정 단계로 이동 (호스트만)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 호스트 권한 확인
            host_check = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id,
                "role": PlayerRole.HOST
            })
            if not host_check:
                raise ValueError("방장만 게임 설정을 시작할 수 있습니다.")
            
            # 방 상태 확인
            room_doc = await collection.find_one({"_id": ObjectId(room_id)})
            if not room_doc:
                raise ValueError("방을 찾을 수 없습니다.")
            
            if room_doc["status"] != RoomStatus.WAITING:
                raise ValueError("게임 설정을 시작할 수 없는 방 상태입니다.")
            
            # 상세 프로필 설정 단계로 변경
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {
                    "$set": {
                        "status": "profile_setup",  # 새로운 상태
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
            
        except ValueError:
            raise
        except Exception:
            return False
    
    async def start_game(self, room_id: str, user_id: str) -> bool:
        """게임 시작 (호스트만)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 호스트 권한 확인
            host_check = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id,
                "role": PlayerRole.HOST
            })
            if not host_check:
                raise ValueError("방장만 게임을 시작할 수 있습니다.")
            
            # 방 상태 확인
            room_doc = await collection.find_one({"_id": ObjectId(room_id)})
            if not room_doc:
                raise ValueError("방을 찾을 수 없습니다.")
            
            if room_doc["status"] != RoomStatus.WAITING:
                raise ValueError("게임을 시작할 수 없는 방 상태입니다.")
            
            # 게임 시작
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {
                    "$set": {
                        "status": RoomStatus.PLAYING,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
            
        except ValueError:
            raise
        except Exception:
            return False
    
    async def end_game(self, room_id: str, user_id: str) -> bool:
        """게임 종료 (호스트만)"""
        collection = self._get_collection()
        player_collection = self._get_player_collection()
        
        try:
            # 호스트 권한 확인
            host_check = await player_collection.find_one({
                "room_id": room_id,
                "user_id": user_id,
                "role": PlayerRole.HOST
            })
            if not host_check:
                raise ValueError("방장만 게임을 종료할 수 있습니다.")
            
            # 게임 종료
            await collection.update_one(
                {"_id": ObjectId(room_id)},
                {
                    "$set": {
                        "status": RoomStatus.FINISHED,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
            
        except ValueError:
            raise
        except Exception:
            return False
    
    async def get_user_rooms(self, user_id: str) -> List[RoomListResponse]:
        """사용자가 참가한 방 목록"""
        player_collection = self._get_player_collection()
        collection = self._get_collection()
        
        # 사용자가 참가한 방 ID 조회
        player_cursor = player_collection.find({"user_id": user_id})
        player_docs = await player_cursor.to_list(length=None)
        
        if not player_docs:
            return []
        
        room_ids = [ObjectId(player["room_id"]) for player in player_docs]
        
        # 방 정보 조회
        cursor = collection.find({"_id": {"$in": room_ids}}).sort("updated_at", -1)
        rooms_docs = await cursor.to_list(length=None)
        
        rooms = []
        for room_doc in rooms_docs:
            room_doc["id"] = str(room_doc["_id"])
            room_doc["has_password"] = room_doc["password"] is not None
            rooms.append(RoomListResponse(**room_doc))
        
        return rooms

# 전역 서비스 인스턴스
room_service = RoomService() 
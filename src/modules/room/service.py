import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from src.modules.user.dto import UserResponse
from .dto import RoomCreateRequest, RoomUpdateRequest, RoomResponse, RoomListResponse
from .models import Room, RoomPlayer, RoomStatus, RoomVisibility, PlayerRole
from .repository import get_room_repository, RoomRepository

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self, room_repository: RoomRepository = None):
        self.room_repository = room_repository or get_room_repository()
        # self.player_repository = ... (추후 분리)
    
    def _hash_password(self, password: str) -> str:
        """방 비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """방 비밀번호 검증"""
        return self._hash_password(password) == hashed_password
    
    def verify_room_password(self, room: RoomResponse, password: str) -> bool:
        if not room.has_password:
            return True
        if not password:
            return False
        return True  # 실제 검증은 add_player_to_room에서 수행
    
    async def create_room(self, room_data: RoomCreateRequest, host_user: UserResponse) -> RoomResponse:
        try:
            logger.info(f"Creating room '{room_data.title}' by user {host_user.username}")
            from .models import Room
            room = Room(
                id=None,
                title=room_data.title,
                description=room_data.description,
                host_id=host_user.id,
                host_username=host_user.username,
                max_players=min(room_data.max_players, 6),
                status=RoomStatus.WAITING,
                visibility=room_data.visibility,
                password_hash=self._hash_password(room_data.password) if room_data.password else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                game_settings=room_data.game_settings or {}
            )
            room_id = await self.room_repository.create(room)
            room.id = room_id
            logger.info(f"Room created successfully: {room_data.title} (ID: {room_id})")
            # 방 생성 후 직접 RoomResponse 반환
            return RoomResponse(**room.model_dump())
        except Exception as e:
            logger.error(f"Error creating room '{room_data.title}': {str(e)}")
            raise
    
    async def get_room(self, room_id: str) -> Optional[RoomResponse]:
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return None
            # 플레이어 목록 등은 추후 PlayerRepository에서 조회
            return RoomResponse(**room.model_dump())
        except Exception:
            return None
    
    async def list_rooms(self, status: Optional[RoomStatus] = None, visibility: Optional[RoomVisibility] = None, search: Optional[str] = None, page: int = 1, limit: int = 20) -> List[RoomListResponse]:
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
        skip = (page - 1) * limit
        rooms = await self.room_repository.find_many(filter_query, skip, limit)
        return [RoomListResponse(**room.model_dump()) for room in rooms]
    # 이하 함수들은 추후 PlayerRepository 분리 후 리팩토링

room_service = RoomService() 
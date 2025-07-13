import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from src.modules.user.dto import UserResponse
from .dto import RoomCreateRequest, RoomUpdateRequest, RoomResponse, RoomListResponse
from .models import Room, RoomPlayer
from .enums import RoomStatus, RoomVisibility, PlayerRole
from .repository import get_room_repository, RoomRepository

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self, room_repository: RoomRepository = None):
        self.room_repository = room_repository or get_room_repository()
        # self.player_repository = ... (추후 분리)
    
    async def create_room(self, room_data: RoomCreateRequest, host_user: UserResponse) -> RoomResponse:
        try:
            logger.info(f"Creating room '{room_data.title}' by user {host_user.username}")
            
            # 최대 인원 검증 (4~6명)
            if not (4 <= room_data.max_players <= 6):
                raise ValueError("방 최대 인원은 4~6명이어야 합니다.")
            
            from .models import Room, RoomPlayer
            now = datetime.utcnow()
            
            # 호스트 플레이어 생성
            host_player = RoomPlayer(
                user_id=host_user.id,
                username=host_user.username,
                role=PlayerRole.HOST,
                joined_at=now
            )
            
            room = Room(
                id=None,
                title=room_data.title,
                description=room_data.description,
                host_id=host_user.id,
                host_username=host_user.username,
                max_players=room_data.max_players,  # 검증된 값 사용
                status=RoomStatus.WAITING,
                visibility=room_data.visibility,
                created_at=now,
                updated_at=now,
                game_settings=room_data.game_settings or {},
                players=[host_player]  # 호스트를 첫 번째 플레이어로 추가
            )
            room_id = await self.room_repository.create(room)
            room.id = room_id
            logger.info(f"Room created successfully: {room_data.title} (ID: {room_id})")
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": [player.model_dump() for player in room.players]
            })
            
            return RoomResponse(**room_data_dict)
        except Exception as e:
            logger.error(f"Error creating room '{room_data.title}': {str(e)}")
            raise
    
    async def get_room(self, room_id: str) -> Optional[RoomResponse]:
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return None
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": [player.model_dump() for player in room.players]
            })
            
            return RoomResponse(**room_data_dict)
        except Exception:
            return None
    
    async def list_rooms(self, status: Optional[RoomStatus] = None, visibility: Optional[RoomVisibility] = None, search: Optional[str] = None, page: int = 1, limit: int = 20, exclude_playing: bool = True) -> List[RoomListResponse]:
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
        
        # 게임 진행 중인 방 제외 (기본값)
        if exclude_playing:
            filter_query["status"] = {"$ne": RoomStatus.PLAYING}
        
        skip = (page - 1) * limit
        rooms = await self.room_repository.find_many(filter_query, skip, limit)
        
        room_list_responses = []
        for room in rooms:
            room_data = room.model_dump()
            room_data.update({
                "current_players": room.current_players  # 실제 플레이어 수
            })
            room_list_responses.append(RoomListResponse(**room_data))
        
        return room_list_responses
    
    async def update_room(self, room_id: str, room_data: RoomUpdateRequest, user_id: str) -> Optional[RoomResponse]:
        """방 설정 변경 (호스트만)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return None
            
            # 호스트 권한 확인
            if room.host_id != user_id:
                raise ValueError("방 설정 변경은 호스트만 가능합니다.")
            
            # 최대 인원 검증 (4~6명)
            if room_data.max_players is not None and not (4 <= room_data.max_players <= 6):
                raise ValueError("방 최대 인원은 4~6명이어야 합니다.")
            
            # 업데이트할 데이터 준비
            update_data = {}
            if room_data.title is not None:
                update_data["title"] = room_data.title
            if room_data.description is not None:
                update_data["description"] = room_data.description
            if room_data.max_players is not None:
                update_data["max_players"] = room_data.max_players
            if room_data.visibility is not None:
                update_data["visibility"] = room_data.visibility
            if room_data.game_settings is not None:
                update_data["game_settings"] = room_data.game_settings
            
            update_data["updated_at"] = datetime.utcnow()
            
            # 방 업데이트
            success = await self.room_repository.update(room_id, update_data)
            if not success:
                return None
            
            # 업데이트된 방 정보 조회
            return await self.get_room(room_id)
            
        except Exception as e:
            logger.error(f"Error updating room '{room_id}': {str(e)}")
            raise
    
    async def start_game(self, room_id: str, user_id: str) -> bool:
        """게임 시작 (호스트만)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return False
            
            # 호스트 권한 확인
            if room.host_id != user_id:
                raise ValueError("게임 시작은 호스트만 가능합니다.")
            
            # 게임 상태를 PLAYING으로 변경
            success = await self.room_repository.update(room_id, {
                "status": RoomStatus.PLAYING,
                "updated_at": datetime.utcnow()
            })
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting game in room '{room_id}': {str(e)}")
            raise
    
    async def add_player_to_room(self, room_id: str, user_id: str, username: str) -> bool:
        """방에 플레이어 추가"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return False
            
            # 게임 진행 중인지 확인
            if room.status == RoomStatus.PLAYING:
                logger.warning(f"Player {username} tried to join room {room_id} while game is in progress")
                return False
            
            # 방이 가득 찼는지 확인
            if room.current_players >= room.max_players:
                return False
            
            # 이미 참가한 플레이어인지 확인 - 이미 있으면 성공으로 처리
            existing_player = room.get_player(user_id)
            if existing_player:
                logger.info(f"Player {username} already in room {room_id}")
                return True  # 이미 있는 사용자는 성공으로 처리
            
            from .models import RoomPlayer
            
            # 새 플레이어 생성
            new_player = RoomPlayer(
                user_id=user_id,
                username=username,
                role=PlayerRole.PLAYER,
                joined_at=datetime.utcnow()
            )
            
            # 방에 플레이어 추가
            if room.add_player(new_player):
                # 데이터베이스 업데이트
                success = await self.room_repository.update(room_id, {
                    "players": [player.model_dump() for player in room.players],
                    "updated_at": datetime.utcnow()
                })
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding player to room '{room_id}': {str(e)}")
            return False
    
    async def remove_player_from_room(self, room_id: str, user_id: str) -> bool:
        """방에서 플레이어 제거"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return False
            
            player = room.get_player(user_id)
            if not player:
                return False
            
            # 호스트가 나가는 경우 방 삭제
            if player.role == PlayerRole.HOST:
                logger.info(f"Host {player.username} is leaving room {room_id}. Deleting room.")
                success = await self.room_repository.delete(room_id)
                return success
            
            # 일반 플레이어 제거
            if room.remove_player(user_id):
                # 데이터베이스 업데이트
                success = await self.room_repository.update(room_id, {
                    "players": [player.model_dump() for player in room.players],
                    "updated_at": datetime.utcnow()
                })
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing player from room '{room_id}': {str(e)}")
            return False
    
    async def get_room_players(self, room_id: str) -> List[RoomPlayer]:
        """방 플레이어 목록 조회"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return []
            
            return room.players
            
        except Exception as e:
            logger.error(f"Error getting players from room '{room_id}': {str(e)}")
            return []
        
    async def get_user_room(self, user_id: str) -> Optional[RoomResponse]:
        """사용자가 참가한 방 조회"""
        try:
            # 사용자가 플레이어로 참가한 방을 조회
            filter_query = {
                "players.user_id": user_id
            }
            rooms = await self.room_repository.find_many(filter_query, 0, 1)
            
            if not rooms:
                return None
            
            room = rooms[0]  # 첫 번째 방만 반환
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": [player.model_dump() for player in room.players]
            })
            
            return RoomResponse(**room_data_dict)
            
        except Exception as e:
            logger.error(f"Error getting user room for user '{user_id}': {str(e)}")
            return None
    
    async def end_game(self, room_id: str, user_id: str) -> bool:
         """게임 종료 (호스트만)"""
         try:
             room = await self.room_repository.find_by_id(room_id)
             if not room:
                 return False
             
             # 호스트 권한 확인
             if room.host_id != user_id:
                 raise ValueError("게임 종료는 호스트만 가능합니다.")
             
             # 게임 상태를 WAITING으로 변경 (다시 입장 가능하도록)
             success = await self.room_repository.update(room_id, {
                 "status": RoomStatus.WAITING,
                 "updated_at": datetime.utcnow()
             })
             
             return success
             
         except Exception as e:
             logger.error(f"Error ending game in room '{room_id}': {str(e)}")
             raise

room_service = RoomService() 
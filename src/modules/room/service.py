import hashlib
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
            logger.info(f"Attempting to get room with ID: {room_id}")
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                logger.warning(f"Room not found with ID: {room_id}")
                return None
            
            logger.info(f"Room found: {room.title} (ID: {room.id})")
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": [player.model_dump() for player in room.players]
            })
            
            return RoomResponse(**room_data_dict)
        except Exception as e:
            logger.error(f"Error getting room {room_id}: {str(e)}")
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
    
    async def start_game(self, room_id: str, user_id: str) -> Optional[str]:
        """게임 시작 - 새로운 게임 방 생성 (호스트만)"""
        try:
            lobby_room = await self.room_repository.find_by_id(room_id)
            if not lobby_room:
                return None
            
            # 호스트 권한 확인
            if lobby_room.host_id != user_id:
                raise ValueError("게임 시작은 호스트만 가능합니다.")
            
            # 로비 방이 WAITING 상태인지 확인
            if lobby_room.status != RoomStatus.WAITING:
                raise ValueError("게임은 대기 중인 방에서만 시작할 수 있습니다.")
            
            # 새로운 게임 방 생성
            from .dto import RoomCreateRequest
            game_room_data = RoomCreateRequest(
                title=f"[GAME] {lobby_room.title}",
                description=f"게임 진행 중: {lobby_room.description or '게임 방'}",
                max_players=lobby_room.max_players,
                visibility=lobby_room.visibility,
                game_settings=lobby_room.game_settings
            )
            
            # 호스트 정보 가져오기
            from src.modules.user.service import user_service
            host_user = await user_service.get_user_by_id(user_id)
            if not host_user:
                raise ValueError("호스트 정보를 찾을 수 없습니다.")
            
            # 게임 방 생성
            game_room = await self.create_room(game_room_data, host_user)
            
            # 로비 방의 모든 플레이어를 게임 방으로 이동
            for player in lobby_room.players:
                await self.add_player_to_room(game_room.id, player.user_id, player.username)
            
            # 로비 방 상태를 PLAYING으로 변경하고 게임 방 ID 연결
            await self.room_repository.update(room_id, {
                "status": RoomStatus.PLAYING,
                "game_room_id": game_room.id,  # 게임 방 ID 저장
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Game started: Lobby room {room_id} -> Game room {game_room.id}")
            return game_room.id
            
        except Exception as e:
            logger.error(f"Error starting game in room '{room_id}': {str(e)}")
            raise
    
    async def add_player_to_room(self, room_id: str, user_id: str, username: str) -> bool:
        """방에 플레이어 추가"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                logger.error(f"Room not found: {room_id}")
                return False
            
            # 이미 참가한 플레이어인지 확인
            existing_player = room.get_player(user_id)
            if existing_player:
                logger.info(f"Player already in room: {user_id}")
                return True  # 이미 있으니까 성공 반환
            
            # 호스트인지 확인 (방 생성자)
            is_host = room.host_id == user_id
            
            # 방이 가득 찼는지 확인
            if room.current_players >= room.max_players:
                logger.error(f"Room is full: {room_id}")
                return False
            
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
                logger.info(f"Successfully added player {username} to room {room_id}")
                return success
            
            logger.error(f"Failed to add player to room: {room_id}")
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
            
            # 호스트는 제거할 수 없음
            player = room.get_player(user_id)
            if not player or player.role == PlayerRole.HOST:
                return False
            
            # 플레이어 제거
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
    
    async def leave_room(self, room_id: str, user_id: str) -> bool:
        """방 나가기 (방장이 나가면 방 삭제)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                logger.error(f"Room not found: {room_id}")
                return False
            
            player = room.get_player(user_id)
            if not player:
                logger.error(f"Player not found in room: {user_id}")
                return False
            
            # 방장이 나가는 경우
            if player.role == PlayerRole.HOST:
                logger.info(f"Host leaving room {room_id}, deleting room...")
                
                # 모든 플레이어에게 방 삭제 알림을 보내기 위해 플레이어 목록 저장
                players_to_notify = room.players.copy()
                
                # 방 삭제 (soft delete)
                success = await self.room_repository.delete(room_id)
                if success:
                    logger.info(f"Room {room_id} deleted successfully")
                    return True
                else:
                    logger.error(f"Failed to delete room {room_id}")
                    return False
            
            # 일반 플레이어가 나가는 경우
            else:
                # 플레이어 제거
                if room.remove_player(user_id):
                    # 데이터베이스 업데이트
                    success = await self.room_repository.update(room_id, {
                        "players": [player.model_dump() for player in room.players],
                        "updated_at": datetime.utcnow()
                    })
                    logger.info(f"Player {user_id} left room {room_id}")
                    return success
                
                logger.error(f"Failed to remove player {user_id} from room {room_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error leaving room '{room_id}': {str(e)}")
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
    
    async def end_game(self, room_id: str, user_id: str) -> bool:
        """게임 종료 - 게임 방을 종료하고 로비로 복귀"""
        try:
            lobby_room = await self.room_repository.find_by_id(room_id)
            if not lobby_room:
                return False
            
            if lobby_room.host_id != user_id:
                raise ValueError("Only host can end the game.")
            
            # 게임 방이 있는지 확인
            if not hasattr(lobby_room, 'game_room_id') or not lobby_room.game_room_id:
                raise ValueError("No active game room found.")
            
            # 게임 방 종료 (삭제 또는 상태 변경)
            game_room = await self.room_repository.find_by_id(lobby_room.game_room_id)
            if game_room:
                # 게임 방을 FINISHED로 변경
                await self.room_repository.update(lobby_room.game_room_id, {
                    "status": RoomStatus.FINISHED,
                    "updated_at": datetime.utcnow()
                })
            
            # 로비 방 상태를 WAITING으로 변경하고 게임 방 ID 제거
            success = await self.room_repository.update(room_id, {
                "status": RoomStatus.WAITING,
                "game_room_id": None,
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Game ended: Game room {lobby_room.game_room_id} -> Lobby room {room_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error ending game in room '{room_id}': {str(e)}")
            raise
    
    async def get_game_room_id(self, lobby_room_id: str) -> Optional[str]:
        """로비 방 ID로 게임 방 ID 조회"""
        try:
            lobby_room = await self.room_repository.find_by_id(lobby_room_id)
            if not lobby_room:
                return None
            
            return getattr(lobby_room, 'game_room_id', None)
            
        except Exception as e:
            logger.error(f"Error getting game room ID for lobby {lobby_room_id}: {str(e)}")
            return None

room_service = RoomService() 
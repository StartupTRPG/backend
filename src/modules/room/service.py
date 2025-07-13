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
    
    async def _get_players_with_profile(self, players) -> List[Dict]:
        """플레이어 목록에 프로필 정보 추가"""
        from .dto import RoomPlayerResponse
        from src.modules.profile.service import user_profile_service
        
        players_with_profile = []
        for player in players:
            # 프로필 정보 조회
            profile = await user_profile_service.get_profile_by_id(player.profile_id)
            if profile:
                player_response = RoomPlayerResponse(
                    profile_id=player.profile_id,
                    display_name=profile.display_name,
                    avatar_url=profile.avatar_url,
                    role=player.role,
                    joined_at=player.joined_at,
                    ready=player.ready
                )
                players_with_profile.append(player_response)
        
        return [player.model_dump() for player in players_with_profile]
    
    async def create_room(self, room_data: RoomCreateRequest, host_user: UserResponse) -> RoomResponse:
        try:
            logger.info(f"Creating room '{room_data.title}' by user {host_user.username}")
            
            # 최대 인원 검증 (4~6명)
            if not (4 <= room_data.max_players <= 6):
                raise ValueError("방 최대 인원은 4~6명이어야 합니다.")
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(host_user.id)
            if not profile:
                raise ValueError("Profile not found. Please create a profile first.")
            
            from .models import Room, RoomPlayer
            now = datetime.utcnow()
            
            # 호스트 플레이어 생성
            host_player = RoomPlayer(
                profile_id=profile.id,
                role=PlayerRole.HOST,
                joined_at=now
            )
            
            room = Room(
                id=None,
                title=room_data.title,
                description=room_data.description,
                host_profile_id=profile.id,
                host_display_name=profile.display_name,
                max_players=room_data.max_players,
                status=RoomStatus.WAITING,
                visibility=room_data.visibility,
                created_at=now,
                updated_at=now,
                game_settings=room_data.game_settings or {},
                players=[host_player]
            )
            room_id = await self.room_repository.create(room)
            room.id = room_id
            logger.info(f"Room created successfully: {room_data.title} (ID: {room_id})")
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": await self._get_players_with_profile(room.players)
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
                "players": await self._get_players_with_profile(room.players)
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
                "current_players": room.current_players
            })
            room_list_responses.append(RoomListResponse(**room_data))
        
        return room_list_responses
    
    async def update_room(self, room_id: str, room_data: RoomUpdateRequest, user_id: str) -> Optional[RoomResponse]:
        """방 정보 업데이트 (user_id 기반)"""
        try:
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                raise ValueError("Profile not found. Please create a profile first.")
            
            return await self.update_room_by_profile_id(room_id, room_data, profile.id)
            
        except Exception as e:
            logger.error(f"Error updating room '{room_id}': {str(e)}")
            raise
    
    async def update_room_by_profile_id(self, room_id: str, room_data: RoomUpdateRequest, profile_id: str) -> Optional[RoomResponse]:
        """방 정보 업데이트 (profile_id 기반)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return None
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_id(profile_id)
            if not profile:
                raise ValueError("Profile not found. Please create a profile first.")
            
            # 호스트 권한 확인
            if room.host_profile_id != profile.id:
                raise ValueError("방 수정은 호스트만 가능합니다.")
            
            # 업데이트할 필드들
            update_fields = {"updated_at": datetime.utcnow()}
            if room_data.title is not None:
                update_fields["title"] = room_data.title
            if room_data.description is not None:
                update_fields["description"] = room_data.description
            if room_data.max_players is not None:
                if not (4 <= room_data.max_players <= 6):
                    raise ValueError("방 최대 인원은 4~6명이어야 합니다.")
                update_fields["max_players"] = room_data.max_players
            if room_data.visibility is not None:
                update_fields["visibility"] = room_data.visibility
            if room_data.game_settings is not None:
                update_fields["game_settings"] = room_data.game_settings
            
            # 데이터베이스 업데이트
            success = await self.room_repository.update(room_id, update_fields)
            if not success:
                return None
            
            # 업데이트된 방 정보 반환
            return await self.get_room(room_id)
            
        except Exception as e:
            logger.error(f"Error updating room '{room_id}': {str(e)}")
            raise

    async def start_game_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """게임 시작 (profile_id 기반)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return False
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_id(profile_id)
            if not profile:
                raise ValueError("Profile not found. Please create a profile first.")
            
            # 호스트 권한 확인
            if room.host_profile_id != profile.id:
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

    async def end_game_by_profile_id(self, room_id: str, profile_id: str) -> bool:
         """게임 종료 (profile_id 기반)"""
         try:
             room = await self.room_repository.find_by_id(room_id)
             if not room:
                 return False
             
             # Profile 정보 조회
             from src.modules.profile.service import user_profile_service
             profile = await user_profile_service.get_profile_by_id(profile_id)
             if not profile:
                 raise ValueError("Profile not found. Please create a profile first.")
             
             # 호스트 권한 확인
             if room.host_profile_id != profile.id:
                 raise ValueError("게임 종료는 호스트만 가능합니다.")
             
             # 모든 플레이어의 ready 상태를 false로 초기화
             for player in room.players:
                 player.ready = False
             
             # 게임 상태를 WAITING으로 변경하고 플레이어 ready 상태도 업데이트
             success = await self.room_repository.update(room_id, {
                 "status": RoomStatus.WAITING,
                 "players": [player.model_dump() for player in room.players],
                 "updated_at": datetime.utcnow()
             })
             
             return success
             
         except Exception as e:
             logger.error(f"Error ending game in room '{room_id}': {str(e)}")
             raise ValueError(f"Error ending game in room '{room_id}': {str(e)}")

    async def add_player_to_room_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """방에 플레이어 추가 (profile_id 기반)"""
        try:
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                return False
            
            # 게임 진행 중인지 확인
            if room.status == RoomStatus.PLAYING:
                logger.warning(f"Player with profile {profile_id} tried to join room {room_id} while game is in progress")
                return False
            
            # 방이 가득 찼는지 확인
            if room.current_players >= room.max_players:
                return False
            
            # 이미 참가한 플레이어인지 확인 - 이미 있으면 성공으로 처리
            existing_player = room.get_player_by_profile_id(profile_id)
            if existing_player:
                logger.info(f"Player with profile {profile_id} already in room {room_id}")
                return True
            
            from .models import RoomPlayer
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            logger.info(f"Looking up profile by ID: {profile_id}")
            profile = await user_profile_service.get_profile_by_id(profile_id)
            if not profile:
                logger.error(f"Profile not found for profile_id: {profile_id}")
                raise ValueError("Profile not found. Please create a profile first.")
            logger.info(f"Found profile: {profile.display_name} (ID: {profile.id})")
            
            # 새 플레이어 생성
            new_player = RoomPlayer(
                profile_id=profile.id,
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

    async def remove_player_from_room_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """방에서 플레이어 제거 (profile_id 기반)"""
        try:
            logger.info(f"Removing player with profile_id {profile_id} from room {room_id}")
            room = await self.room_repository.find_by_id(room_id)
            if not room:
                logger.warning(f"Room {room_id} not found")
                return False
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_id(profile_id)
            if not profile:
                logger.warning(f"Profile {profile_id} not found")
                return False
            
            logger.info(f"Found profile: {profile.display_name} (ID: {profile.id})")
            player = room.get_player_by_profile_id(profile.id)
            if not player:
                logger.warning(f"Player not found in room for profile {profile.id}")
                return False
            
            logger.info(f"Found player: role={player.role}, profile_id={player.profile_id}")
            
            # 호스트가 나가는 경우 방 삭제
            if player.role == PlayerRole.HOST:
                logger.info(f"Host {profile.display_name} is leaving room {room_id}. Deleting room.")
                success = await self.room_repository.delete(room_id)
                logger.info(f"Room deletion result: {success}")
                return success
            
            # 일반 플레이어 제거
            if room.remove_player_by_profile_id(profile.id):
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
        
    async def get_joined_room_by_profile_id(self, profile_id: str) -> Optional[RoomResponse]:
        """프로필이 참가한 방 조회 (profile_id 기반)"""
        try:
            # 프로필이 플레이어로 참가한 방을 조회
            filter_query = {
                "players.profile_id": profile_id
            }
            rooms = await self.room_repository.find_many(filter_query, 0, 1)
            
            if not rooms:
                return None
            
            room = rooms[0]
            
            # RoomResponse에 필요한 필드들을 추가하여 반환
            room_data_dict = room.model_dump()
            room_data_dict.update({
                "current_players": room.current_players,
                "players": await self._get_players_with_profile(room.players)
            })
            
            return RoomResponse(**room_data_dict)
            
        except Exception as e:
            logger.error(f"Error getting user room for profile '{profile_id}': {str(e)}")
            return None
    
    async def set_player_ready(self, room_id: str, profile_id: str, ready: bool) -> bool:
        """플레이어 레디 상태 변경 (호스트는 불가)"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        player = room.get_player_by_profile_id(profile_id)
        if not player or player.role == PlayerRole.HOST:
            return False
        player.ready = ready
        await self.room_repository.update(room_id, {"players": [p.model_dump() for p in room.players]})
        return True

    async def is_all_ready(self, room_id: str) -> bool:
        """호스트 제외 모든 플레이어가 레디인지 확인"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        for player in room.players:
            if player.role != PlayerRole.HOST and not player.ready:
                return False
        return True

room_service = RoomService() 
import logging
from datetime import datetime
from typing import Optional, List, Dict
from src.modules.user.dto import UserResponse
from .dto import RoomCreateRequest, RoomUpdateRequest, RoomResponse, RoomListResponse
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
    
    async def get_room(self, room_id: str) -> Optional[RoomResponse]:
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
        # Profile 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        if not profile:
            raise ValueError("Profile not found. Please create a profile first.")
        
        return await self.update_room_by_profile_id(room_id, room_data, profile.id)
    
    async def update_room_by_profile_id(self, room_id: str, room_data: RoomUpdateRequest, profile_id: str) -> Optional[RoomResponse]:
        """방 정보 업데이트 (profile_id 기반)"""
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

    async def start_game_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """게임 시작 (profile_id 기반)"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 호스트 권한 확인
        if room.host_profile_id != profile_id:
            return False
        
        # 모든 플레이어를 자동으로 준비 상태로 설정
        for player in room.players:
            player.ready = True
        
        # 방 상태를 게임 진행 중으로 변경
        success = await self.room_repository.update(room_id, {
            "status": RoomStatus.PLAYING,
            "players": [player.model_dump() for player in room.players],
            "updated_at": datetime.utcnow()
        })
        
        if success:
            logger.info(f"Game started in room: {room_id}")
        
        return success
    
    async def end_game_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """게임 종료 (profile_id 기반)"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 호스트 권한 확인
        if room.host_profile_id != profile_id:
            return False
        
        # 방 상태를 대기 중으로 변경
        success = await self.room_repository.update(room_id, {
            "status": RoomStatus.WAITING,
            "updated_at": datetime.utcnow()
        })
        
        if success:
            logger.info(f"Game ended in room: {room_id}")
        
        return success

    async def add_player_to_room_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """방에 플레이어 추가 (profile_id 기반)"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 방이 가득 찼는지 확인
        if room.current_players >= room.max_players:
            return False
        
        # 이미 참가 중인지 확인
        for player in room.players:
            if player.profile_id == profile_id:
                return False
        
        # Profile 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_id(profile_id)
        if not profile:
            return False
        
        # 새 플레이어 추가
        from .models import RoomPlayer
        new_player = RoomPlayer(
            profile_id=profile_id,
            role=PlayerRole.PLAYER,
            joined_at=datetime.utcnow()
        )
        
        # 플레이어 목록에 추가
        room.players.append(new_player)
        
        # 데이터베이스 업데이트
        success = await self.room_repository.update(room_id, {
            "players": [player.model_dump() for player in room.players],
            "updated_at": datetime.utcnow()
        })
        
        if success:
            logger.info(f"Player {profile.display_name} joined room: {room_id}")
        
        return success

    async def remove_player_from_room_by_profile_id(self, room_id: str, profile_id: str) -> bool:
        """방에서 플레이어 제거 (profile_id 기반)"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 플레이어 찾기
        player_to_remove = None
        for player in room.players:
            if player.profile_id == profile_id:
                player_to_remove = player
                break
        
        if not player_to_remove:
            return False
        
        # 호스트인 경우 방 삭제
        if player_to_remove.role == PlayerRole.HOST:
            success = await self.room_repository.delete(room_id)
            if success:
                logger.info(f"Host left, room deleted: {room_id}")
            return success
        
        # 일반 플레이어인 경우 제거
        room.players.remove(player_to_remove)
        
        # 데이터베이스 업데이트
        success = await self.room_repository.update(room_id, {
            "players": [player.model_dump() for player in room.players],
            "updated_at": datetime.utcnow()
        })
        
        if success:
            logger.info(f"Player {profile_id} left room: {room_id}")
        
        return success

    async def get_joined_room_by_profile_id(self, profile_id: str) -> Optional[RoomResponse]:
        """프로필 ID로 참가 중인 방 조회"""
        room = await self.room_repository.find_by_profile_id(profile_id)
        if not room:
            return None
        
        # RoomResponse에 필요한 필드들을 추가하여 반환
        room_data_dict = room.model_dump()
        room_data_dict.update({
            "current_players": room.current_players,
            "players": await self._get_players_with_profile(room.players)
        })
        
        return RoomResponse(**room_data_dict)

    async def set_player_ready(self, room_id: str, profile_id: str, ready: bool) -> bool:
        """플레이어 준비 상태 설정"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 플레이어 찾기
        for player in room.players:
            if player.profile_id == profile_id:
                player.ready = ready
                break
        
        # 데이터베이스 업데이트
        success = await self.room_repository.update(room_id, {
            "players": [player.model_dump() for player in room.players],
            "updated_at": datetime.utcnow()
        })
        
        return success

    async def is_all_ready(self, room_id: str) -> bool:
        """모든 플레이어가 준비되었는지 확인"""
        room = await self.room_repository.find_by_id(room_id)
        if not room:
            return False
        
        # 모든 플레이어가 준비되었는지 확인
        for player in room.players:
            if not player.ready:
                return False
        
        return True

# 전역 서비스 인스턴스
room_service = RoomService() 
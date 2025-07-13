from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..enums import RoomStatus, RoomVisibility, PlayerRole
from .room_player import RoomPlayer

class Room(BaseModel):
    """방 데이터베이스 스키마"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    host_profile_id: str  # host_id 대신 host_profile_id 사용
    host_display_name: str  # host_username 대신 host_display_name 사용
    max_players: int
    status: RoomStatus
    visibility: RoomVisibility
    created_at: datetime
    updated_at: datetime
    game_settings: dict = {}
    players: List[RoomPlayer] = []  # 방에 있는 플레이어 목록
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    @property
    def current_players(self) -> int:
        """현재 플레이어 수"""
        return len(self.players)
    
    @property
    def host_player(self) -> Optional[RoomPlayer]:
        """호스트 플레이어 정보"""
        for player in self.players:
            if player.role == PlayerRole.HOST:
                return player
        return None
    
    def add_player(self, player: RoomPlayer) -> bool:
        """플레이어 추가"""
        if self.current_players >= self.max_players:
            return False
        
        # 이미 있는 플레이어인지 확인
        for existing_player in self.players:
            if existing_player.profile_id == player.profile_id:
                return False
        
        self.players.append(player)
        return True
    
    def remove_player_by_profile_id(self, profile_id: str) -> bool:
        """플레이어 제거 (profile_id로)"""
        for i, player in enumerate(self.players):
            if player.profile_id == profile_id:
                self.players.pop(i)
                return True
        return False
    
    def get_player_by_profile_id(self, profile_id: str) -> Optional[RoomPlayer]:
        """특정 플레이어 조회 (profile_id로)"""
        for player in self.players:
            if player.profile_id == profile_id:
                return player
        return None
    
    class Config:
        from_attributes = True 
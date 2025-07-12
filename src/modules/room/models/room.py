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
    host_id: str
    host_username: str
    max_players: int
    status: RoomStatus
    visibility: RoomVisibility
    password_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    game_settings: dict = {}
    players: List[RoomPlayer] = []  # 방에 있는 플레이어 목록
    
    @property
    def has_password(self) -> bool:
        """방에 비밀번호가 있는지 확인"""
        return self.password_hash is not None
    
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
            if existing_player.user_id == player.user_id:
                return False
        
        self.players.append(player)
        return True
    
    def remove_player(self, user_id: str) -> bool:
        """플레이어 제거"""
        for i, player in enumerate(self.players):
            if player.user_id == user_id:
                self.players.pop(i)
                return True
        return False
    
    def get_player(self, user_id: str) -> Optional[RoomPlayer]:
        """특정 플레이어 조회"""
        for player in self.players:
            if player.user_id == user_id:
                return player
        return None
    
    class Config:
        from_attributes = True 
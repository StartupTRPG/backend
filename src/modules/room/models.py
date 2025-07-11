from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class RoomStatus(str, Enum):
    WAITING = "waiting"          # 대기 중 (로비)
    PROFILE_SETUP = "profile_setup"  # 상세 프로필 설정 중
    PLAYING = "playing"          # 게임 진행 중
    FINISHED = "finished"        # 게임 종료

class RoomVisibility(str, Enum):
    PUBLIC = "public"        # 공개 방
    PRIVATE = "private"      # 비공개 방

class PlayerRole(str, Enum):
    HOST = "host"           # 방장
    PLAYER = "player"       # 플레이어
    OBSERVER = "observer"   # 관찰자





class RoomPlayer(BaseModel):
    user_id: str
    username: str
    role: PlayerRole
    joined_at: datetime
    
    @property
    def is_host(self) -> bool:
        return self.role == PlayerRole.HOST

class RoomCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_players: int = 6
    visibility: RoomVisibility = RoomVisibility.PUBLIC
    password: str  # 비밀번호 필수
    game_settings: dict = {}

# RoomJoin 모델 제거 - Socket.IO에서 직접 처리
# socket.emit('join_room', { room_id: 'xxx', password: 'xxx' })

class RoomUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    max_players: Optional[int] = None
    visibility: Optional[RoomVisibility] = None
    password: Optional[str] = None
    game_settings: Optional[dict] = None

class RoomResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    host_id: str
    host_username: str
    current_players: int
    max_players: int
    status: RoomStatus
    visibility: RoomVisibility
    has_password: bool
    created_at: datetime
    updated_at: datetime
    game_settings: dict
    players: List[RoomPlayer]
    
    class Config:
        from_attributes = True

class RoomListResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    host_username: str
    current_players: int
    max_players: int
    status: RoomStatus
    visibility: RoomVisibility
    has_password: bool
    created_at: datetime
    
    class Config:
        from_attributes = True 
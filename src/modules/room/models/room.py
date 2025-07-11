from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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

class Room(BaseModel):
    """방 데이터베이스 스키마"""
    id: str
    title: str
    description: Optional[str] = None
    host_id: str
    host_username: str
    max_players: int
    status: RoomStatus
    visibility: RoomVisibility
    password_hash: str
    created_at: datetime
    updated_at: datetime
    game_settings: dict = {}
    
    class Config:
        from_attributes = True

class RoomPlayer(BaseModel):
    """방 플레이어 데이터베이스 스키마"""
    user_id: str
    username: str
    role: PlayerRole
    joined_at: datetime
    
    @property
    def is_host(self) -> bool:
        return self.role == PlayerRole.HOST
    
    class Config:
        from_attributes = True

class GameProfile(BaseModel):
    """게임 프로필 데이터베이스 스키마"""
    id: Optional[str] = None
    user_id: str
    room_id: str
    character_name: str
    is_detailed: bool = False
    character_class: Optional[str] = None
    character_level: Optional[int] = None
    character_description: Optional[str] = None
    character_stats: Optional[Dict[str, Any]] = None
    character_role: Optional[str] = None
    character_avatar: Optional[str] = None
    character_equipment: Optional[Dict[str, Any]] = None
    character_skills: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GameProfileCreate(BaseModel):
    """게임 프로필 생성 요청"""
    character_name: str
    character_class: str
    character_level: int = 1
    character_description: Optional[str] = None
    character_stats: Optional[Dict[str, Any]] = None
    character_role: Optional[str] = None
    character_avatar: Optional[str] = None
    character_equipment: Optional[Dict[str, Any]] = None
    character_skills: Optional[List[str]] = None

class LobbyProfileCreate(BaseModel):
    """로비 프로필 생성 요청 (이름만)"""
    character_name: str 
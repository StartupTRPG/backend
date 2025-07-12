from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..enums import RoomStatus, RoomVisibility
from .room_player_response import RoomPlayerResponse

class RoomResponse(BaseModel):
    """방 상세 응답 DTO"""
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
    players: List[RoomPlayerResponse]
    
    class Config:
        from_attributes = True 
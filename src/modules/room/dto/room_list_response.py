from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models import RoomStatus, RoomVisibility

class RoomListResponse(BaseModel):
    """방 목록 응답 DTO"""
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
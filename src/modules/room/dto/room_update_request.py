from pydantic import BaseModel
from typing import Optional
from ..models import RoomVisibility

class RoomUpdateRequest(BaseModel):
    """방 수정 요청 DTO"""
    title: Optional[str] = None
    description: Optional[str] = None
    max_players: Optional[int] = None
    visibility: Optional[RoomVisibility] = None
    password: Optional[str] = None
    game_settings: Optional[dict] = None 
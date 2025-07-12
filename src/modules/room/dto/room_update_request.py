from pydantic import BaseModel, Field
from typing import Optional
from ..enums import RoomVisibility

class RoomUpdateRequest(BaseModel):
    """방 수정 요청 DTO"""
    title: Optional[str] = None
    description: Optional[str] = None
    max_players: Optional[int] = Field(None, ge=4, le=6, description="방 최대 인원 (4~6명)")
    visibility: Optional[RoomVisibility] = None
    game_settings: Optional[dict] = None 
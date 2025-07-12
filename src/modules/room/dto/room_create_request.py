from pydantic import BaseModel, Field
from typing import Optional
from ..enums import RoomVisibility

class RoomCreateRequest(BaseModel):
    """방 생성 요청 DTO"""
    title: str
    description: Optional[str] = None
    max_players: int = Field(default=6, ge=4, le=6, description="방 최대 인원 (4~6명)")
    visibility: RoomVisibility = RoomVisibility.PUBLIC

    game_settings: dict = {} 
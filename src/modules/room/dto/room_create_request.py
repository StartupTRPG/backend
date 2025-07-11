from pydantic import BaseModel
from typing import Optional
from ..models import RoomVisibility

class RoomCreateRequest(BaseModel):
    """방 생성 요청 DTO"""
    title: str
    description: Optional[str] = None
    max_players: int = 6
    visibility: RoomVisibility = RoomVisibility.PUBLIC
    password: str  # 비밀번호 필수
    game_settings: dict = {} 
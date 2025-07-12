from pydantic import BaseModel
from datetime import datetime
from ..enums import PlayerRole

class RoomPlayerResponse(BaseModel):
    """방 플레이어 응답 DTO"""
    user_id: str
    username: str
    role: PlayerRole
    joined_at: datetime
    is_host: bool
    
    class Config:
        from_attributes = True 
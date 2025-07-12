from pydantic import BaseModel, Field
from datetime import datetime
from ..enums import PlayerRole


class RoomPlayerResponse(BaseModel):
    """방 플레이어 응답 모델"""
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    role: PlayerRole = Field(..., description="플레이어 역할")
    joined_at: datetime = Field(..., description="참가 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439012",
                "username": "testuser",
                "role": "host",
                "joined_at": "2024-01-01T00:00:00"
            }
        } 
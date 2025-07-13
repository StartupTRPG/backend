from pydantic import BaseModel, Field
from datetime import datetime
from ..enums import PlayerRole


class RoomPlayerResponse(BaseModel):
    """방 플레이어 응답 모델"""
    profile_id: str = Field(..., description="프로필 ID")
    display_name: str = Field(..., description="표시 이름")
    role: PlayerRole = Field(..., description="플레이어 역할")
    joined_at: datetime = Field(..., description="참가 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "507f1f77bcf86cd799439012",
                "display_name": "스타트업 마스터",
                "role": "host",
                "joined_at": "2024-01-01T00:00:00"
            }
        } 
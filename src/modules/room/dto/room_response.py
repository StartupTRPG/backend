from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..enums import RoomStatus, RoomVisibility, PlayerRole
from .room_player_response import RoomPlayerResponse


class RoomResponse(BaseModel):
    """방 정보 응답 모델"""
    id: str = Field(..., description="방 ID")
    title: str = Field(..., description="방 제목")
    description: str = Field(..., description="방 설명")
    host_id: str = Field(..., description="호스트 사용자 ID")
    host_username: str = Field(..., description="호스트 사용자명")
    max_players: int = Field(..., ge=4, le=6, description="최대 플레이어 수")
    current_players: int = Field(..., ge=1, description="현재 플레이어 수")
    status: RoomStatus = Field(..., description="방 상태")
    visibility: RoomVisibility = Field(..., description="방 공개 설정")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")
    game_settings: Dict[str, Any] = Field(default_factory=dict, description="게임 설정")
    players: List[RoomPlayerResponse] = Field(..., description="플레이어 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "스타트업 TRPG 방",
                "description": "스타트업을 테마로 한 TRPG 게임입니다. 창업 아이디어를 구상하고 팀을 만들어보세요!",
                "host_id": "507f1f77bcf86cd799439012",
                "host_username": "startup_master",
                "max_players": 4,
                "current_players": 2,
                "status": "waiting",
                "visibility": "public",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:30:00",
                "game_settings": {
                    "game_duration": 120,
                    "difficulty": "medium",
                    "theme": "tech_startup"
                },
                "players": [
                    {
                        "user_id": "507f1f77bcf86cd799439012",
                        "username": "startup_master",
                        "role": "host",
                        "joined_at": "2024-01-01T12:00:00"
                    },
                    {
                        "user_id": "507f1f77bcf86cd799439013",
                        "username": "tech_enthusiast",
                        "role": "player",
                        "joined_at": "2024-01-01T12:15:00"
                    }
                ]
            }
        } 
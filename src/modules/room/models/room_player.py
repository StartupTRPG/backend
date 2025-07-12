from pydantic import BaseModel
from datetime import datetime
from ..enums import PlayerRole

class RoomPlayer(BaseModel):
    """방 플레이어 데이터베이스 스키마"""
    user_id: str
    username: str
    role: PlayerRole
    joined_at: datetime
    is_host: bool = False  # 프로퍼티 대신 필드로 추가
    
    def __init__(self, **data):
        super().__init__(**data)
        # role이 HOST인 경우 is_host를 True로 설정
        if self.role == PlayerRole.HOST:
            self.is_host = True
    
    class Config:
        from_attributes = True 
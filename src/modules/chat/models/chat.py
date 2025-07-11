from pydantic import BaseModel
from datetime import datetime
from src.modules.chat.enum import ChatType

class ChatMessage(BaseModel):
    """채팅 메시지 데이터베이스 스키마"""
    id: str
    room_id: str
    username: str
    display_name: str
    message_type: ChatType
    content: str  # 암호화된 내용이 저장됨
    timestamp: datetime
    
    class Config:
        from_attributes = True 
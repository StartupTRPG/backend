from pydantic import BaseModel
from datetime import datetime
from src.modules.chat.enum import ChatType

class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답 DTO"""
    id: str
    room_id: str
    user_id: str
    username: str
    display_name: str
    message_type: ChatType
    message: str  # 복호화된 내용
    timestamp: datetime
    encrypted: bool = False
    
    class Config:
        from_attributes = True 
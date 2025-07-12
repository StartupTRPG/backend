from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .models.socket_event_type import SocketEventType

class BaseSocketMessage(BaseModel):
    """기본 Socket 메시지 모델"""
    event_type: SocketEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True

# 구체적인 메시지 모델들
class AuthMessage(BaseSocketMessage):
    """인증 메시지"""
    token: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None

class RoomMessage(BaseSocketMessage):
    """방 관련 메시지"""
    room_id: str
    password: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None

class ChatMessage(BaseSocketMessage):
    """채팅 메시지"""
    room_id: str
    user_id: str
    username: str
    display_name: str
    message: str
    message_type: str = "text"
    encrypted: bool = False

class SystemMessage(BaseSocketMessage):
    """시스템 메시지"""
    room_id: str
    content: str
    message_type: str = "system" 
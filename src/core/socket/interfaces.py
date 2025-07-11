from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class SocketEventType(str, Enum):
    """Socket 이벤트 타입"""
    # 인증 관련
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    CONNECT_SUCCESS = "connect_success"
    
    # 방 관련
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_JOINED = "room_joined"
    ROOM_LEFT = "room_left"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    GET_ROOM_USERS = "get_room_users"
    ROOM_USERS = "room_users"
    
    # 채팅 관련
    SEND_MESSAGE = "send_message"
    NEW_MESSAGE = "new_message"
    GET_CHAT_HISTORY = "get_chat_history"
    CHAT_HISTORY = "chat_history"
    SYSTEM_MESSAGE = "system_message"
    
    # 공통
    ERROR = "error"

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
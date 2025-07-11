from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"           # 일반 텍스트 메시지
    SYSTEM = "system"       # 시스템 메시지 (입장/퇴장 알림 등)
    EMOJI = "emoji"         # 이모지 메시지
    IMAGE = "image"         # 이미지 메시지

class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    id: Optional[str] = None
    room_id: str = Field(..., description="방 ID")
    user_id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    display_name: str = Field(..., description="표시 이름")
    message_type: MessageType = Field(MessageType.TEXT, description="메시지 타입")
    content: str = Field(..., min_length=1, max_length=1000, description="메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    
    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    """채팅 메시지 생성 요청"""
    room_id: str = Field(..., description="방 ID")
    message_type: MessageType = Field(MessageType.TEXT, description="메시지 타입")
    content: str = Field(..., min_length=1, max_length=1000, description="메시지 내용")

class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답"""
    id: str
    room_id: str
    user_id: str
    username: str
    display_name: str
    message_type: MessageType
    content: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

class SystemMessage(BaseModel):
    """시스템 메시지"""
    room_id: str
    message_type: MessageType = MessageType.SYSTEM
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RoomChatHistory(BaseModel):
    """방 채팅 기록"""
    room_id: str
    messages: List[ChatMessageResponse]
    total_count: int
    page: int
    limit: int 
from pydantic import BaseModel, Field
from src.modules.chat.enum import ChatType

class ChatMessageCreateRequest(BaseModel):
    """채팅 메시지 생성 요청 DTO"""
    room_id: str = Field(..., description="방 ID")
    message_type: ChatType = Field(ChatType.TEXT, description="메시지 타입")
    content: str = Field(..., min_length=1, max_length=1000, description="메시지 내용") 
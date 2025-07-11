from pydantic import BaseModel, Field

class ChatMessageSendRequest(BaseModel):
    """채팅 메시지 전송 요청 DTO (Socket.IO용)"""
    message: str = Field(..., min_length=1, max_length=1000, description="메시지 내용")
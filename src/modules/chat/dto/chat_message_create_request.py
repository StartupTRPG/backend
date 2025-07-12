from pydantic import BaseModel, Field
from src.modules.chat.enum import ChatType

class ChatMessageCreateRequest(BaseModel):
    """Chat message creation request DTO"""
    room_id: str = Field(..., description="Room ID")
    message_type: ChatType = Field(ChatType.LOBBY, description="Message type")
    content: str = Field(..., min_length=1, max_length=1000, description="Message content") 
from pydantic import BaseModel, Field

class ChatMessageSendRequest(BaseModel):
    """Chat message send request DTO (for Socket.IO)"""
    message: str = Field(..., min_length=1, max_length=1000, description="Message content")
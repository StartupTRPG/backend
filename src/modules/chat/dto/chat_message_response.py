from pydantic import BaseModel
from datetime import datetime
from src.modules.chat.enums import ChatType

class ChatMessageResponse(BaseModel):
    """Chat message response DTO"""
    id: str
    room_id: str
    profile_id: str
    display_name: str
    message_type: ChatType
    message: str
    timestamp: datetime
    encrypted: bool = False
    
    class Config:
        from_attributes = True 
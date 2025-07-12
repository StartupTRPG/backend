from pydantic import BaseModel
from datetime import datetime
from src.modules.chat.enum import ChatType

class ChatMessageResponse(BaseModel):
    """Chat message response DTO"""
    id: str
    room_id: str
    user_id: str
    username: str
    display_name: str
    message_type: ChatType
    message: str  # Decrypted content
    timestamp: datetime
    chat_category: str = "general"  # "lobby", "game", "general"
    encrypted: bool = False
    
    class Config:
        from_attributes = True 
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from src.modules.chat.enum import ChatType

class ChatMessage(BaseModel):
    """Chat message database schema"""
    id: Optional[str] = None
    room_id: str
    username: str
    display_name: str
    message_type: ChatType
    content: str  # Encrypted content is stored
    timestamp: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
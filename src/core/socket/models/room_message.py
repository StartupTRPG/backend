from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .socket_event_type import SocketEventType

class RoomMessage(BaseModel):
    """방 관련 메시지"""
    event_type: SocketEventType
    room_id: str
    profile_id: Optional[str] = None
    host_profile_id: Optional[str] = None
    host_display_name: Optional[str] = None
    username: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
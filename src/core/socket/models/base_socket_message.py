from typing import Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from .socket_event_type import SocketEventType

class BaseSocketMessage(BaseModel):
    """Base Socket message model"""
    event_type: SocketEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True 
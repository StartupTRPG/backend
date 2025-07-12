from typing import Optional
from .base_socket_message import BaseSocketMessage

class RoomMessage(BaseSocketMessage):
    """방 관련 메시지"""
    room_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None 
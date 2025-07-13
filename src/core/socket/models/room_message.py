from typing import Optional
from .base_socket_message import BaseSocketMessage

class RoomMessage(BaseSocketMessage):
    """방 관련 메시지"""
    room_id: str
    profile_id: Optional[str] = None
    host_profile_id: Optional[str] = None
    host_display_name: Optional[str] = None
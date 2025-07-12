from .base_socket_message import BaseSocketMessage

class SystemMessage(BaseSocketMessage):
    """System message"""
    room_id: str
    content: str
    message_type: str = "system" 
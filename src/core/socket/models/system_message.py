from .base_socket_message import BaseSocketMessage

class SystemMessage(BaseSocketMessage):
    """시스템 메시지"""
    room_id: str
    content: str
    message_type: str = "system" 
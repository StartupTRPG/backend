from .base_socket_message import BaseSocketMessage

class ChatMessage(BaseSocketMessage):
    """채팅 메시지"""
    room_id: str
    user_id: str
    username: str
    display_name: str
    message: str
    message_type: str = "text"
    encrypted: bool = False 
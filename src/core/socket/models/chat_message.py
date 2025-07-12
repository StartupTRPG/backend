from .base_socket_message import BaseSocketMessage

class ChatMessage(BaseSocketMessage):
    """Chat message"""
    room_id: str
    user_id: str
    username: str
    display_name: str
    message: str
    message_type: str = "text"
    encrypted: bool = False 
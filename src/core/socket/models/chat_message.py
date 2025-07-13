from .base_socket_message import BaseSocketMessage

class ChatMessage(BaseSocketMessage):
    """Chat message"""
    room_id: str
    profile_id: str  
    display_name: str
    message: str
    message_type: str = "text"
    encrypted: bool = False 
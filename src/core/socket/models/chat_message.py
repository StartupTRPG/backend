from .base_socket_message import BaseSocketMessage
from src.modules.chat.enums import ChatType

class ChatMessage(BaseSocketMessage):
    """Chat message"""
    room_id: str
    profile_id: str  
    display_name: str
    message: str
    message_type: ChatType
    encrypted: bool = False 
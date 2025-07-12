from typing import Optional
from .base_socket_message import BaseSocketMessage

class AuthMessage(BaseSocketMessage):
    """인증 메시지"""
    token: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None 
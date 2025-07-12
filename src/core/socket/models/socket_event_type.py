from enum import Enum

class SocketEventType(str, Enum):
    """Socket 이벤트 타입"""
    # 인증 관련
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    CONNECT_SUCCESS = "connect_success"
    
    # 방 관련
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    
    # 채팅 관련
    LOBBY_MESSAGE = "lobby_message"
    SYSTEM_MESSAGE = "system_message"
    GAME_MESSAGE = "game_message"
    
    # 공통
    ERROR = "error"
    FORCE_DISCONNECT = "force_disconnect" 
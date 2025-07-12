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
    ROOM_JOINED = "room_joined"
    ROOM_LEFT = "room_left"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    GET_ROOM_USERS = "get_room_users"
    ROOM_USERS = "room_users"
    
    # 채팅 관련
    SEND_MESSAGE = "send_message"
    NEW_MESSAGE = "new_message"
    GET_CHAT_HISTORY = "get_chat_history"
    CHAT_HISTORY = "chat_history"
    SYSTEM_MESSAGE = "system_message"
    
    # 공통
    ERROR = "error"
    FORCE_DISCONNECT = "force_disconnect" 
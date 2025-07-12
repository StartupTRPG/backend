from enum import Enum

class ChatType(str, Enum):
    TEXT = "text"           # General text message
    SYSTEM = "system"       # System message (join/leave notifications, etc.)
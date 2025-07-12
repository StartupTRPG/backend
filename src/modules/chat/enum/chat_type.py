from enum import Enum

class ChatType(str, Enum):
    LOBBY = "lobby"         # Lobby chat (when room status is WAITING)
    GAME = "game"           # Game chat (when room status is PLAYING)
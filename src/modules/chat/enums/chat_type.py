from enum import Enum

class ChatType(str, Enum):
    LOBBY = "lobby"         # Lobby chat message
    GAME = "game"           # Game chat message
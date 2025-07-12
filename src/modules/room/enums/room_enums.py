from enum import Enum

class RoomStatus(str, Enum):
    WAITING = "waiting"          # 대기 중 (로비)
    PLAYING = "playing"          # 게임 진행 중
    FINISHED = "finished"        # 게임 종료

class RoomVisibility(str, Enum):
    PUBLIC = "public"        # 공개 방
    PRIVATE = "private"      # 비공개 방

class PlayerRole(str, Enum):
    HOST = "host"           # 방장
    PLAYER = "player"       # 플레이어
    OBSERVER = "observer"   # 관찰자 
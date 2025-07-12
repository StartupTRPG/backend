from enum import Enum

class ChatType(str, Enum):
    TEXT = "text"           # 일반 텍스트 메시지
    SYSTEM = "system"       # 시스템 메시지 (입장/퇴장 알림 등) 
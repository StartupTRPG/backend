from pydantic import BaseModel

class ChatHistoryRequest(BaseModel):
    """채팅 기록 조회 요청 DTO"""
    room_id: str
    page: int = 1
    limit: int = 50 
from pydantic import BaseModel
from typing import List
from .chat_message_response import ChatMessageResponse

class RoomChatHistoryResponse(BaseModel):
    """방 채팅 기록 응답 DTO"""
    room_id: str
    messages: List[ChatMessageResponse]
    total_count: int
    page: int
    limit: int 
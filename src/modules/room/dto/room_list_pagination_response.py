from pydantic import BaseModel
from typing import List
from .room_list_response import RoomListResponse

class RoomListPaginationResponse(BaseModel):
    """방 목록 페이지네이션 응답 DTO"""
    rooms: List[RoomListResponse]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool 
from typing import List, Optional
from pydantic import BaseModel, Field
from .base_socket_message import BaseSocketMessage


class AgendaVoteRequest(BaseModel):
    """아젠다 투표 요청 메시지"""
    agenda_id: str = Field(..., description="투표할 아젠다 ID")
    selected_option_id: str = Field(..., description="선택된 옵션 ID")
    room_id: str = Field(..., description="방 ID")


class AgendaVoteResponse(BaseModel):
    """아젠다 투표 응답 메시지"""
    success: bool = Field(..., description="투표 성공 여부")
    message: str = Field(..., description="응답 메시지")
    agenda_id: str = Field(..., description="아젠다 ID")
    vote: str = Field(..., description="투표 선택")
    total_votes: int = Field(..., description="총 투표 수")
    vote_results: dict = Field(..., description="투표 결과")


class AgendaVoteUpdate(BaseModel):
    """아젠다 투표 업데이트 메시지 (다른 사용자들에게 전송)"""
    agenda_id: str = Field(..., description="아젠다 ID")
    voter_id: str = Field(..., description="투표자 ID")
    vote: str = Field(..., description="투표 선택")
    total_votes: int = Field(..., description="총 투표 수")
    vote_results: dict = Field(..., description="투표 결과")
    is_complete: bool = Field(..., description="투표 완료 여부") 
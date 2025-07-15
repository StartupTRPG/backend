from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Player(BaseModel):
    """플레이어 정보"""
    id: str = Field(..., description="플레이어 ID")
    name: str = Field(..., description="플레이어 이름")

class GameRequest(BaseModel):
    """게임 생성 요청"""
    player_list: List[Player] = Field(..., description="플레이어 리스트")

class CreateContextRequest(BaseModel):
    """컨텍스트 생성 요청"""
    max_turn: int = Field(..., description="최대 턴 수")
    story: str = Field(..., description="게임 스토리")
    player_list: List[Player] = Field(..., description="플레이어 리스트")

class PlayerContext(BaseModel):
    """플레이어 컨텍스트"""
    id: str = Field(..., description="플레이어 ID")
    name: str = Field(..., description="플레이어 이름")
    role: str = Field(..., description="플레이어 역할")
    context: Dict[str, str] = Field(..., description="플레이어 컨텍스트")

class CreateAgendaRequest(BaseModel):
    """아젠다 생성 요청"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")

class CreateTaskRequest(BaseModel):
    """태스크 생성 요청"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")

class CreateOvertimeRequest(BaseModel):
    """오버타임 생성 요청"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")

class UpdateContextRequest(BaseModel):
    """컨텍스트 업데이트 요청"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")
    agenda_list: List[Dict[str, Any]] = Field(..., description="아젠다 리스트")
    task_list: Dict[str, List[Dict[str, Any]]] = Field(..., description="태스크 리스트")
    overtime_task_list: Dict[str, List[Dict[str, Any]]] = Field(..., description="오버타임 태스크 리스트")

class ExplanationRequest(BaseModel):
    """설명 생성 요청"""
    company_context: Dict[str, Any] = Field(..., description="회사 컨텍스트")
    player_context_list: List[Dict[str, Any]] = Field(..., description="플레이어 컨텍스트 리스트")

class ResultRequest(BaseModel):
    """결과 계산 요청"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[Dict[str, Any]] = Field(..., description="플레이어 컨텍스트 리스트") 
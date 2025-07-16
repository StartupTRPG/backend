from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class GameResponse(BaseModel):
    """게임 생성 응답"""
    story: str = Field(..., description="생성된 스토리")

class PlayerContext(BaseModel):
    """플레이어 컨텍스트"""
    id: str
    name: str
    role: str
    context: Dict[str, str] # key: 일자, value: 플레이어 상태 설명

class PlayerContextOutput(BaseModel):
    """플레이어 컨텍스트 출력"""
    player_id: str = Field(..., description="플레이어 ID")
    player_name: str = Field(..., description="플레이어 이름")
    player_role: str = Field(..., description="플레이어 역할")
    player_context: Dict[str, str] = Field(..., description="플레이어 컨텍스트")

class CreateContextResponse(BaseModel):
    """컨텍스트 생성 응답"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")

class AgendaOption(BaseModel):
    """아젠다 옵션"""
    id: str
    text: str
    impact_summary: str

class Agenda(BaseModel):
    """아젠다"""
    id: str
    name: str
    description: str
    options: List[AgendaOption]

class AgendaOutput(BaseModel):
    """아젠다 출력"""
    agenda_id: str = Field(..., description="아젠다 ID")
    agenda_name: str = Field(..., description="아젠다 이름")
    agenda_description: str = Field(..., description="아젠다 설명")
    agenda_options: List[AgendaOption] = Field(..., description="아젠다 옵션 리스트")

class CreateAgendaResponse(BaseModel):
    """아젠다 생성 응답"""
    description: str = Field(..., description="설명")
    agenda_list: List[Agenda] = Field(..., description="아젠다 리스트")

class TaskOption(BaseModel):
    """태스크 옵션"""
    id: str
    text: str
    impact_summary: str

class Task(BaseModel):
    """태스크"""
    id: str
    name: str
    description: str
    options: List[TaskOption]

class TaskOptionOutput(BaseModel):
    """태스크 옵션 출력"""
    task_option_id: str = Field(..., description="태스크 옵션 ID")
    task_option_text: str = Field(..., description="태스크 옵션 텍스트")
    task_option_impact_summary: str = Field(..., description="태스크 옵션 영향 요약")

class TaskOutput(BaseModel):
    """태스크 출력"""
    task_id: str = Field(..., description="태스크 ID")
    task_name: str = Field(..., description="태스크 이름")
    task_description: str = Field(..., description="태스크 설명")
    task_options: List[TaskOptionOutput] = Field(..., description="태스크 옵션 리스트")

class CreateTaskResponse(BaseModel):
    """태스크 생성 응답"""
    task_list: Dict[str, List[Task]] = Field(..., description="태스크 리스트")

class OvertimeTaskType(str, Enum):
    """오버타임 태스크 타입"""
    OVERTIME = "overtime"
    REST = "rest"

class OvertimeTaskOption(BaseModel):
    """오버타임 태스크 옵션"""
    id: str
    text: str
    impact_summary: str

class OvertimeTask(BaseModel):
    """오버타임 태스크"""
    id: str
    type: OvertimeTaskType
    name: str
    description: str
    options: List[OvertimeTaskOption]

class OvertimeTaskOptionOutput(BaseModel):
    """오버타임 태스크 옵션 출력"""
    overtime_task_option_id: str = Field(..., description="오버타임 태스크 옵션 ID")
    overtime_task_option_text: str = Field(..., description="오버타임 태스크 옵션 텍스트")
    overtime_task_option_impact_summary: str = Field(..., description="오버타임 태스크 옵션 영향 요약")

class OvertimeTaskOutput(BaseModel):
    """오버타임 태스크 출력"""
    overtime_task_id: str = Field(..., description="오버타임 태스크 ID")
    overtime_task_type: OvertimeTaskType = Field(..., description="오버타임 태스크 타입")
    overtime_task_name: str = Field(..., description="오버타임 태스크 이름")
    overtime_task_description: str = Field(..., description="오버타임 태스크 설명")
    overtime_task_options: List[OvertimeTaskOptionOutput] = Field(..., description="오버타임 태스크 옵션 리스트")

class CreateOvertimeResponse(BaseModel):
    """오버타임 생성 응답"""
    task_list: Dict[str, List[OvertimeTask]] = Field(..., description="태스크 리스트")

class UpdateContextResponse(BaseModel):
    """컨텍스트 업데이트 응답"""
    company_context: Dict[str, str] = Field(..., description="회사 컨텍스트")
    player_context_list: List[PlayerContext] = Field(..., description="플레이어 컨텍스트 리스트")

class ExplanationResponse(BaseModel):
    """설명 생성 응답"""
    explanation: str = Field(..., description="설명")

class GameResult(BaseModel):
    """게임 결과"""
    success: bool = Field(..., description="성공 여부")
    summary: str = Field(..., description="요약")

class PlayerRanking(BaseModel):
    """플레이어 랭킹"""
    rank: int = Field(..., description="랭킹")
    id: str
    name: str
    role: str
    evaluation: str

class ResultResponse(BaseModel):
    """결과 계산 응답"""
    game_result: Dict[str, Any] = Field(..., description="게임 결과")
    player_rankings: List[PlayerRanking] = Field(..., description="플레이어 랭킹 리스트") 

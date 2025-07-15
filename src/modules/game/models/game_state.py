from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class GamePhase(str, Enum):
    """게임 단계"""
    WAITING = "waiting"  # 대기 중
    STORY_CREATION = "story_creation"  # 스토리 생성
    CONTEXT_CREATION = "context_creation"  # 컨텍스트 생성
    AGENDA_CREATION = "agenda_creation"  # 아젠다 생성
    TASK_CREATION = "task_creation"  # 태스크 생성
    OVERTIME_CREATION = "overtime_creation"  # 오버타임 생성
    PLAYING = "playing"  # 게임 진행 중
    CONTEXT_UPDATE = "context_update"  # 컨텍스트 업데이트
    EXPLANATION = "explanation"  # 설명 생성
    RESULT = "result"  # 결과 계산
    FINISHED = "finished"  # 게임 종료

class GameState(BaseModel):
    """게임 상태 모델"""
    room_id: str
    phase: GamePhase = GamePhase.WAITING
    current_turn: int = 0
    max_turn: int = 0
    
    # 플레이어 정보 추가
    player_list: List[Dict[str, str]] = []
    
    # 게임 데이터
    story: Optional[str] = None
    company_context: Dict[str, str] = {}
    player_context_list: List[Dict[str, Any]] = []
    
    # 게임 요소들
    agenda_list: List[Dict[str, Any]] = []
    task_list: Dict[str, List[Dict[str, Any]]] = {}
    overtime_task_list: Dict[str, List[Dict[str, Any]]] = {}
    
    # 플레이어 선택 사항들
    agenda_selections: Dict[str, Dict[str, Any]] = {}  # player_id -> selected_agenda
    task_selections: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}  # player_id -> selected_tasks
    overtime_selections: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}  # player_id -> selected_overtime
    
    # 결과
    explanation: Optional[str] = None
    game_result: Optional[Dict[str, Any]] = None
    player_rankings: List[Dict[str, Any]] = []
    
    # 메타데이터
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """타임스탬프 업데이트"""
        self.updated_at = datetime.utcnow()
    
    def is_phase_complete(self, phase: GamePhase) -> bool:
        """특정 단계가 완료되었는지 확인"""
        phase_order = list(GamePhase)
        current_index = phase_order.index(self.phase)
        target_index = phase_order.index(phase)
        return current_index > target_index
    
    def can_proceed_to_phase(self, phase: GamePhase) -> bool:
        """특정 단계로 진행할 수 있는지 확인"""
        phase_order = list(GamePhase)
        current_index = phase_order.index(self.phase)
        target_index = phase_order.index(phase)
        
        # 컨텍스트 생성 단계에서 아젠다 생성으로 진행하는 경우
        if self.phase == GamePhase.CONTEXT_CREATION and phase == GamePhase.AGENDA_CREATION:
            return True
        
        return target_index == current_index + 1 
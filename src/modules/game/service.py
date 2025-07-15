import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.modules.game.llm_client import llm_client
from src.modules.game.models.game_state import GameState, GamePhase
from src.modules.game.dto.game_requests import *
from src.modules.game.dto.game_responses import *

logger = logging.getLogger(__name__)

class GameService:
    """LLM 게임 서비스"""
    
    def __init__(self):
        self.active_games: Dict[str, GameState] = {}  # room_id -> GameState
    
    def get_game_state(self, room_id: str) -> Optional[GameState]:
        """게임 상태 조회"""
        return self.active_games.get(room_id)
    
    def create_game_state(self, room_id: str) -> GameState:
        """새로운 게임 상태 생성"""
        game_state = GameState(room_id=room_id)
        self.active_games[room_id] = game_state
        logger.info(f"새로운 게임 상태 생성: {room_id}")
        return game_state
    
    def remove_game_state(self, room_id: str):
        """게임 상태 제거"""
        if room_id in self.active_games:
            del self.active_games[room_id]
            logger.info(f"게임 상태 제거: {room_id}")
    
    async def start_game(self, room_id: str, player_list: List[Dict[str, str]]) -> GameResponse:
        """게임 시작 - 스토리 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                game_state = self.create_game_state(room_id)
            
            # LLM 서버에 게임 생성 요청
            response = await llm_client.create_game(player_list)
            
            # 게임 상태 업데이트
            game_state.story = response.get("story")
            game_state.phase = GamePhase.CONTEXT_CREATION
            game_state.update_timestamp()
            
            logger.info(f"게임 시작 성공: {room_id}")
            return GameResponse(story=game_state.story)
            
        except Exception as e:
            logger.error(f"게임 시작 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def create_context(self, room_id: str, max_turn: int) -> CreateContextResponse:
        """컨텍스트 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.CONTEXT_CREATION):
                raise Exception("컨텍스트 생성 단계로 진행할 수 없습니다.")
            
            # 플레이어 리스트 구성 (실제 구현에서는 방의 플레이어 정보를 사용)
            player_list = [
                {"id": "player1", "name": "플레이어1"},
                {"id": "player2", "name": "플레이어2"}
            ]
            
            # LLM 서버에 컨텍스트 생성 요청
            response = await llm_client.create_context(
                max_turn=max_turn,
                story=game_state.story,
                player_list=player_list
            )
            
            # 게임 상태 업데이트
            game_state.company_context = response.get("company_context", {})
            game_state.player_context_list = response.get("player_context_list", [])
            game_state.max_turn = max_turn
            game_state.phase = GamePhase.AGENDA_CREATION
            game_state.update_timestamp()
            
            logger.info(f"컨텍스트 생성 성공: {room_id}")
            return CreateContextResponse(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
        except Exception as e:
            logger.error(f"컨텍스트 생성 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def create_agenda(self, room_id: str) -> CreateAgendaResponse:
        """아젠다 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.AGENDA_CREATION):
                raise Exception("아젠다 생성 단계로 진행할 수 없습니다.")
            
            # LLM 서버에 아젠다 생성 요청
            response = await llm_client.create_agenda(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
            # 게임 상태 업데이트
            game_state.agenda_list = response.get("agenda_list", [])
            game_state.phase = GamePhase.TASK_CREATION
            game_state.update_timestamp()
            
            logger.info(f"아젠다 생성 성공: {room_id}")
            return CreateAgendaResponse(
                description=response.get("description", ""),
                agenda_list=game_state.agenda_list
            )
            
        except Exception as e:
            logger.error(f"아젠다 생성 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def create_task(self, room_id: str) -> CreateTaskResponse:
        """태스크 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.TASK_CREATION):
                raise Exception("태스크 생성 단계로 진행할 수 없습니다.")
            
            # LLM 서버에 태스크 생성 요청
            response = await llm_client.create_task(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
            # 게임 상태 업데이트
            game_state.task_list = response.get("task_list", {})
            game_state.phase = GamePhase.OVERTIME_CREATION
            game_state.update_timestamp()
            
            logger.info(f"태스크 생성 성공: {room_id}")
            return CreateTaskResponse(task_list=game_state.task_list)
            
        except Exception as e:
            logger.error(f"태스크 생성 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def create_overtime(self, room_id: str) -> CreateOvertimeResponse:
        """오버타임 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.OVERTIME_CREATION):
                raise Exception("오버타임 생성 단계로 진행할 수 없습니다.")
            
            # LLM 서버에 오버타임 생성 요청
            response = await llm_client.create_overtime(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
            # 게임 상태 업데이트
            game_state.overtime_task_list = response.get("task_list", {})
            game_state.phase = GamePhase.PLAYING
            game_state.started_at = datetime.utcnow()
            game_state.update_timestamp()
            
            logger.info(f"오버타임 생성 성공: {room_id}")
            return CreateOvertimeResponse(task_list=game_state.overtime_task_list)
            
        except Exception as e:
            logger.error(f"오버타임 생성 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def update_context(self, room_id: str, agenda_selections: Dict[str, Any], 
                           task_selections: Dict[str, Any], overtime_selections: Dict[str, Any]) -> UpdateContextResponse:
        """컨텍스트 업데이트"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if game_state.phase != GamePhase.PLAYING:
                raise Exception("게임 진행 중이 아닙니다.")
            
            # 플레이어 선택 사항 저장
            game_state.agenda_selections = agenda_selections
            game_state.task_selections = task_selections
            game_state.overtime_selections = overtime_selections
            
            # LLM 서버에 컨텍스트 업데이트 요청
            response = await llm_client.update_context(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list,
                agenda_list=game_state.agenda_list,
                task_list=game_state.task_list,
                overtime_task_list=game_state.overtime_task_list
            )
            
            # 게임 상태 업데이트
            game_state.company_context = response.get("company_context", {})
            game_state.player_context_list = response.get("player_context_list", [])
            game_state.phase = GamePhase.EXPLANATION
            game_state.update_timestamp()
            
            logger.info(f"컨텍스트 업데이트 성공: {room_id}")
            return UpdateContextResponse(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
        except Exception as e:
            logger.error(f"컨텍스트 업데이트 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def create_explanation(self, room_id: str) -> ExplanationResponse:
        """설명 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.EXPLANATION):
                raise Exception("설명 생성 단계로 진행할 수 없습니다.")
            
            # LLM 서버에 설명 생성 요청
            response = await llm_client.create_explanation(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
            # 게임 상태 업데이트
            game_state.explanation = response.get("explanation", "")
            game_state.phase = GamePhase.RESULT
            game_state.update_timestamp()
            
            logger.info(f"설명 생성 성공: {room_id}")
            return ExplanationResponse(explanation=game_state.explanation)
            
        except Exception as e:
            logger.error(f"설명 생성 실패: {room_id}, 오류: {str(e)}")
            raise
    
    async def calculate_result(self, room_id: str) -> ResultResponse:
        """결과 계산"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.RESULT):
                raise Exception("결과 계산 단계로 진행할 수 없습니다.")
            
            # LLM 서버에 결과 계산 요청
            response = await llm_client.calculate_result(
                company_context=game_state.company_context,
                player_context_list=game_state.player_context_list
            )
            
            # 게임 상태 업데이트
            game_state.game_result = response.get("game_result", {})
            game_state.player_rankings = response.get("player_rankings", [])
            game_state.phase = GamePhase.FINISHED
            game_state.finished_at = datetime.utcnow()
            game_state.update_timestamp()
            
            logger.info(f"결과 계산 성공: {room_id}")
            return ResultResponse(
                game_result=game_state.game_result,
                player_rankings=game_state.player_rankings
            )
            
        except Exception as e:
            logger.error(f"결과 계산 실패: {room_id}, 오류: {str(e)}")
            raise
    
    def get_game_progress(self, room_id: str) -> Dict[str, Any]:
        """게임 진행 상황 조회"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            return {"error": "게임 상태를 찾을 수 없습니다."}
        
        return {
            "room_id": room_id,
            "phase": game_state.phase,
            "current_turn": game_state.current_turn,
            "max_turn": game_state.max_turn,
            "story": game_state.story,
            "company_context": game_state.company_context,
            "player_context_list": game_state.player_context_list,
            "agenda_list": game_state.agenda_list,
            "task_list": game_state.task_list,
            "overtime_task_list": game_state.overtime_task_list,
            "explanation": game_state.explanation,
            "game_result": game_state.game_result,
            "player_rankings": game_state.player_rankings,
            "created_at": game_state.created_at.isoformat(),
            "updated_at": game_state.updated_at.isoformat(),
            "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
            "finished_at": game_state.finished_at.isoformat() if game_state.finished_at else None
        }

# 전역 게임 서비스 인스턴스
game_service = GameService() 
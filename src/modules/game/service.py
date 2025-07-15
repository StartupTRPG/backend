import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.modules.game.llm_client import llm_client
from src.modules.game.models.game_state import GameState, GamePhase
from src.modules.game.dto.game_requests import *
from src.modules.game.dto.game_responses import *
import asyncio

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
    
    async def create_game(self, room_id: str, players: List[Dict[str, str]]) -> Dict[str, Any]:
        """게임 생성 - 스토리 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                game_state = self.create_game_state(room_id)
            
            # LLM 서버에 게임 생성 요청 (story만 생성)
            response = await llm_client.create_game(players)
            
            # 게임 상태 업데이트
            game_state.story = response.get("story")
            game_state.phase = GamePhase.STORY_CREATION  # story_creation 단계로 설정
            game_state.update_timestamp()
            
            logger.info(f"게임 생성 성공: {room_id}")
            return {
                "room_id": room_id,
                "story": game_state.story,
                "phase": game_state.phase.value if hasattr(game_state.phase, 'value') else str(game_state.phase)
            }
            
        except Exception as e:
            logger.error(f"게임 생성 실패: {room_id}, 오류: {str(e)}")
            raise

    async def start_game(self, room_id: str, player_list: List[Dict[str, str]]) -> GameResponse:
        """게임 시작 (스토리 생성)"""
        try:
            # 게임 상태 생성
            game_state = self.create_game_state(room_id)
            game_state.phase = GamePhase.STORY_CREATION
            game_state.player_list = player_list  # 플레이어 리스트 저장
            
            # LLM 서버에 게임 시작 요청 (create_game 메서드 사용)
            response = await llm_client.create_game(player_list)
            
            # 게임 상태 업데이트
            game_state.story = response.get("story", "")
            game_state.max_turn = response.get("max_turn", 10)
            game_state.update_timestamp()
            
            logger.info(f"게임 시작 성공: {room_id}")
            
            # 백그라운드에서 컨텍스트 생성 시작
            asyncio.create_task(self._create_context_background(room_id))
            
            return GameResponse(story=game_state.story)
            
        except Exception as e:
            logger.error(f"게임 시작 실패: {room_id}, 오류: {str(e)}")
            raise

    async def _create_context_background(self, room_id: str):
        """백그라운드에서 컨텍스트 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state or not game_state.story:
                return
            
            logger.info(f"백그라운드 컨텍스트 생성 시작: {room_id}")
            
            # LLM 서버에 컨텍스트 생성 요청
            context_response = await llm_client.create_context(
                max_turn=game_state.max_turn,
                story=game_state.story,
                player_list=game_state.player_list  # 저장된 플레이어 리스트 사용
            )
            
            # 게임 상태 업데이트
            game_state.company_context = context_response.get("company_context", {})
            game_state.player_context_list = context_response.get("player_context_list", [])
            game_state.phase = GamePhase.CONTEXT_CREATION
            game_state.update_timestamp()
            
            logger.info(f"백그라운드 컨텍스트 생성 완료: {room_id}")
            
            # 컨텍스트 생성 완료 브로드캐스트
            from src.core.socket.server import sio
            await sio.emit('context_created', {
                'room_id': room_id,
                'company_context': game_state.company_context,
                'player_context_list': game_state.player_context_list,
                'message': '컨텍스트가 생성되었습니다.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
            
        except Exception as e:
            logger.error(f"백그라운드 컨텍스트 생성 실패: {room_id}, 오류: {str(e)}")
    
    async def create_context(self, room_id: str, max_turn: int, story: str) -> CreateContextResponse:
        """컨텍스트 생성"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            if not game_state.can_proceed_to_phase(GamePhase.CONTEXT_CREATION):
                raise Exception("컨텍스트 생성 단계로 진행할 수 없습니다.")
            
            # 실제 방의 플레이어 정보 가져오기
            from src.modules.room.service import room_service
            room = await room_service.get_room(room_id)
            if not room:
                raise Exception("방 정보를 찾을 수 없습니다.")
            
            # 플레이어 리스트를 LLM 형식으로 변환
            player_list = []
            for player in room.players:
                player_list.append({
                    "id": player.profile_id,
                    "name": player.display_name
                })
            
            # LLM 서버에 컨텍스트 생성 요청 (story를 기반으로 생성)
            response = await llm_client.create_context(
                max_turn=max_turn,
                story=story,  # story를 매개변수로 전달
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
            
            # 컨텍스트가 아직 생성 중이면 완료될 때까지 대기
            if not game_state.company_context or not game_state.player_context_list:
                logger.info(f"컨텍스트 생성 완료 대기 중: {room_id}")
                
                # 최대 30초 대기
                max_wait_time = 30
                wait_time = 0
                while (not game_state.company_context or not game_state.player_context_list) and wait_time < max_wait_time:
                    await asyncio.sleep(1)
                    wait_time += 1
                    game_state = self.get_game_state(room_id)  # 최신 상태 다시 가져오기
                
                if not game_state.company_context or not game_state.player_context_list:
                    raise Exception("컨텍스트 생성 시간 초과")
                
                logger.info(f"컨텍스트 생성 완료 확인: {room_id}")
            
            # 이제 아젠다 생성 진행
            if not game_state.can_proceed_to_phase(GamePhase.AGENDA_CREATION):
                # 컨텍스트 생성 단계에서 아젠다 생성으로 바로 진행
                if game_state.phase == GamePhase.CONTEXT_CREATION:
                    pass  # 컨텍스트가 생성되었으므로 아젠다 생성 가능
                else:
                    raise Exception("아젠다 생성 단계로 진행할 수 없습니다.")
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 아젠다 생성 요청
            response = await llm_client.create_agenda(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list
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
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 태스크 생성 요청
            response = await llm_client.create_task(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list
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
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 오버타임 생성 요청
            response = await llm_client.create_overtime(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list
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
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 컨텍스트 업데이트 요청
            response = await llm_client.update_context(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list,
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
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 설명 생성 요청
            response = await llm_client.create_explanation(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list
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
            
            # LLM 서버가 기대하는 형식으로 player_context_list 변환
            formatted_player_context_list = []
            for player_context in game_state.player_context_list:
                formatted_player_context_list.append({
                    "id": player_context.get("player_id", ""),
                    "name": player_context.get("display_name", ""),
                    "role": player_context.get("role", ""),
                    "context": player_context.get("context", {})
                })
            
            # LLM 서버에 결과 계산 요청
            response = await llm_client.calculate_result(
                company_context=game_state.company_context,
                player_context_list=formatted_player_context_list
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
    
    async def finish_game(self, room_id: str) -> Dict[str, Any]:
        """게임 종료"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                raise Exception("게임 상태를 찾을 수 없습니다.")
            
            # 게임 상태를 종료로 변경
            game_state.phase = GamePhase.FINISHED
            game_state.finished_at = datetime.utcnow()
            game_state.update_timestamp()
            
            # 게임 상태 제거
            self.remove_game_state(room_id)
            
            logger.info(f"게임 종료 성공: {room_id}")
            return {
                "room_id": room_id,
                "status": "finished"
            }
            
        except Exception as e:
            logger.error(f"게임 종료 실패: {room_id}, 오류: {str(e)}")
            raise

    def get_game_progress(self, room_id: str) -> Dict[str, Any]:
        """게임 진행 상황 조회"""
        try:
            game_state = self.get_game_state(room_id)
            if not game_state:
                return {"error": "게임 상태를 찾을 수 없습니다."}
            
            return {
                "room_id": room_id,
                "phase": game_state.phase.value if hasattr(game_state.phase, 'value') else str(game_state.phase),
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
                "created_at": game_state.created_at.isoformat() if game_state.created_at else None,
                "updated_at": game_state.updated_at.isoformat() if game_state.updated_at else None,
                "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
                "finished_at": game_state.finished_at.isoformat() if game_state.finished_at else None
            }
        except Exception as e:
            logger.error(f"게임 진행 상황 조회 중 오류 발생: {room_id}, 오류: {str(e)}")
            return {"error": f"게임 진행 상황 조회 실패: {str(e)}"}

# 전역 게임 서비스 인스턴스
game_service = GameService() 
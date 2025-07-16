import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.modules.game.llm_client import llm_client
from src.modules.game.models.game_state import GameState, GamePhase
from src.modules.game.dto.game_requests import *
from src.modules.game.dto.game_responses import *
from src.core.mongodb import get_collection
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

    async def start_game(self, room_id: str, player_list: List[Dict[str, str]]) -> GameResponse:
        """게임 시작 (스토리 생성)"""
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

    async def _create_context_background(self, room_id: str):
        """백그라운드에서 컨텍스트 생성"""
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
    
    async def create_context(self, room_id: str, max_turn: int, story: str) -> CreateContextResponse:
        """컨텍스트 생성"""
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
                "name": player.display_name,
                "role": player.role if hasattr(player, 'role') else "개발자"  # 기본값 설정
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
    
    async def create_agenda(self, room_id: str) -> CreateAgendaResponse:
        """아젠다 생성"""
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
        formatted_player_context_list = game_state.player_context_list
        
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
    
    async def create_task(self, room_id: str) -> CreateTaskResponse:
        """태스크 생성 - LLM 백엔드에서 생성"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        if not game_state.can_proceed_to_phase(GamePhase.TASK_CREATION):
            raise Exception("태스크 생성 단계로 진행할 수 없습니다.")
        
        # LLM 백엔드를 통한 태스크 생성
        from .task_generation_service import task_generation_service
        task_list = await task_generation_service.generate_tasks_for_room(room_id)
        
        # 게임 상태 업데이트
        game_state.task_list = task_list
        game_state.phase = GamePhase.OVERTIME_CREATION
        game_state.update_timestamp()
        
        logger.info(f"LLM 백엔드를 통한 태스크 생성 성공: {room_id}")
        return CreateTaskResponse(task_list=task_list)
    
    async def create_overtime(self, room_id: str) -> CreateOvertimeResponse:
        """오버타임 생성"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        if not game_state.can_proceed_to_phase(GamePhase.OVERTIME_CREATION):
            raise Exception("오버타임 생성 단계로 진행할 수 없습니다.")
        
        # LLM 서버가 기대하는 형식으로 player_context_list 변환
        formatted_player_context_list = game_state.player_context_list
        
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
    
    async def update_context(self, room_id: str, agenda_selections: Dict[str, Any], 
                           task_selections: Dict[str, Any], overtime_selections: Dict[str, Any]) -> UpdateContextResponse:
        """컨텍스트 업데이트"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        # 플레이어 선택 사항 저장
        game_state.agenda_selections = agenda_selections
        game_state.task_selections = task_selections
        game_state.overtime_selections = overtime_selections
        
        # context_update 모듈용 key로 변환 (이미 딕셔너리인 경우 처리)
        formatted_player_context_list = []
        for pc in game_state.player_context_list:
            if isinstance(pc, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                formatted_player_context_list.append(pc)
            else:
                # Pydantic 모델인 경우 변환
                formatted_player_context_list.append({
                    'id': pc.id,
                    'name': pc.name,
                    'role': pc.role,
                    'context': pc.context
                })
        
        # 선택 정보를 포함한 agenda_list 생성
        agenda_list_with_selections = []
        for agenda in game_state.agenda_list:
            if isinstance(agenda, dict):
                # 이미 딕셔너리인 경우
                agenda_dict = agenda.copy()
                agenda_dict['selected_options'] = {}
                
                # 해당 agenda의 선택 정보 추가
                for player_id, selected_option_id in agenda_selections.items():
                    # 선택된 옵션 찾기
                    selected_option = None
                    for option in agenda.get('options', []):
                        if option.get('id') == selected_option_id:
                            selected_option = option
                            break
                    
                    if selected_option:
                        agenda_dict['selected_options'][player_id] = selected_option
            else:
                # Pydantic 모델인 경우
                agenda_dict = {
                    'id': agenda.id,
                    'name': agenda.name,
                    'description': agenda.description,
                    'selected_options': {}
                }
                
                # 해당 agenda의 선택 정보 추가
                for player_id, selected_option_id in agenda_selections.items():
                    # 선택된 옵션 찾기
                    selected_option = None
                    for option in agenda.options:
                        if option.id == selected_option_id:
                            selected_option = {
                                'id': option.id,
                                'text': option.text,
                                'impact_summary': option.impact_summary
                            }
                            break
                    
                    if selected_option:
                        agenda_dict['selected_options'][player_id] = selected_option
            
            agenda_list_with_selections.append(agenda_dict)
        
        # 선택 정보를 포함한 task_list 생성
        task_list_with_selections = {}
        for player_id, task_list in game_state.task_list.items():
            task_list_with_selections[player_id] = []
            player_task_selections = task_selections.get(player_id, [])
            
            for task in task_list:
                if isinstance(task, dict):
                    # 이미 딕셔너리인 경우
                    task_dict = task.copy()
                    task_dict['selected_option'] = None
                    
                    # 해당 플레이어가 선택한 옵션 찾기
                    for selected_option_id in player_task_selections:
                        for option in task.get('options', []):
                            if option.get('id') == selected_option_id:
                                task_dict['selected_option'] = option
                                break
                else:
                    # Pydantic 모델인 경우
                    task_dict = {
                        'id': task.id,
                        'name': task.name,
                        'description': task.description,
                        'selected_option': None
                    }
                    
                    # 해당 플레이어가 선택한 옵션 찾기
                    for selected_option_id in player_task_selections:
                        for option in task.options:
                            if option.id == selected_option_id:
                                task_dict['selected_option'] = {
                                    'id': option.id,
                                    'text': option.text,
                                    'impact_summary': option.impact_summary
                                }
                                break
                
                task_list_with_selections[player_id].append(task_dict)
        
        # 선택 정보를 포함한 overtime_task_list 생성
        overtime_task_list_with_selections = {}
        for player_id, overtime_task_list in game_state.overtime_task_list.items():
            overtime_task_list_with_selections[player_id] = []
            player_overtime_selections = overtime_selections.get(player_id, [])
            
            for overtime_task in overtime_task_list:
                if isinstance(overtime_task, dict):
                    # 이미 딕셔너리인 경우
                    overtime_task_dict = overtime_task.copy()
                    overtime_task_dict['selected_option'] = None
                    
                    # 해당 플레이어가 선택한 옵션 찾기
                    for selected_option_id in player_overtime_selections:
                        for option in overtime_task.get('options', []):
                            if option.get('id') == selected_option_id:
                                overtime_task_dict['selected_option'] = option
                                break
                else:
                    # Pydantic 모델인 경우
                    overtime_task_dict = {
                        'id': overtime_task.id,
                        'type': overtime_task.type.value,
                        'name': overtime_task.name,
                        'description': overtime_task.description,
                        'options': [
                            {
                                'id': option.id,
                                'text': option.text,
                                'impact_summary': option.impact_summary
                            }
                            for option in overtime_task.options
                        ],
                        'selected_option': None
                    }
                    
                    # 해당 플레이어가 선택한 옵션 찾기
                    for selected_option_id in player_overtime_selections:
                        for option in overtime_task.options:
                            if option.id == selected_option_id:
                                overtime_task_dict['selected_option'] = {
                                    'id': option.id,
                                    'text': option.text,
                                    'impact_summary': option.impact_summary
                                }
                                break
                
                overtime_task_list_with_selections[player_id].append(overtime_task_dict)
        
        # LLM 서버에 컨텍스트 업데이트 요청
        response = await llm_client.update_context(
            company_context=game_state.company_context,
            player_context_list=formatted_player_context_list,
            agenda_list=agenda_list_with_selections,
            task_list=task_list_with_selections,
            overtime_task_list=overtime_task_list_with_selections
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
    
    async def create_explanation(self, room_id: str) -> ExplanationResponse:
        """설명 생성"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        # explanation 모듈용 key로 변환 (이미 딕셔너리인 경우 처리)
        formatted_player_context_list = []
        for pc in game_state.player_context_list:
            if isinstance(pc, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                formatted_player_context_list.append(pc)
            else:
                # Pydantic 모델인 경우 변환
                formatted_player_context_list.append({
                    'id': pc.id,
                    'name': pc.name,
                    'role': pc.role,
                    'context': pc.context
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
    
    async def calculate_result(self, room_id: str) -> ResultResponse:
        """결과 계산"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        # result 모듈용 key로 변환 (이미 딕셔너리인 경우 처리)
        formatted_player_context_list = []
        for pc in game_state.player_context_list:
            if isinstance(pc, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                formatted_player_context_list.append(pc)
            else:
                # Pydantic 모델인 경우 변환
                formatted_player_context_list.append({
                    'id': pc.id,
                    'name': pc.name,
                    'role': pc.role,
                    'context': pc.context
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
    
    async def finish_game(self, room_id: str) -> Dict[str, Any]:
        """게임 종료"""
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

    def get_game_progress(self, room_id: str) -> Dict[str, Any]:
        """게임 진행 상황 조회"""
        game_state = self.get_game_state(room_id)
        if not game_state:
            return {"error": "게임 상태를 찾을 수 없습니다."}
        
        # Task 객체를 딕셔너리로 변환하는 함수
        def convert_task_to_dict(task):
            return {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'options': [
                    {
                        'id': option.id,
                        'text': option.text,
                        'impact_summary': option.impact_summary
                    }
                    for option in task.options
                ]
            }
        
        # OvertimeTask 객체를 딕셔너리로 변환하는 함수
        def convert_overtime_task_to_dict(task):
            return {
                'id': task.id,
                'type': task.type.value,
                'name': task.name,
                'description': task.description,
                'options': [
                    {
                        'id': option.id,
                        'text': option.text,
                        'impact_summary': option.impact_summary
                    }
                    for option in task.options
                ]
            }
        
        # Agenda 객체를 딕셔너리로 변환하는 함수
        def convert_agenda_to_dict(agenda):
            return {
                'id': agenda.id,
                'name': agenda.name,
                'description': agenda.description,
                'options': [
                    {
                        'id': option.id,
                        'text': option.text,
                        'impact_summary': option.impact_summary
                    }
                    for option in agenda.options
                ]
            }
        
        # PlayerContext 객체를 딕셔너리로 변환하는 함수
        def convert_player_context_to_dict(player_context):
            return {
                'id': player_context.id,
                'name': player_context.name,
                'role': player_context.role,
                'context': player_context.context
            }
        
        # PlayerRanking 객체를 딕셔너리로 변환하는 함수
        def convert_player_ranking_to_dict(player_ranking):
            return {
                'rank': player_ranking.rank,
                'id': player_ranking.id,
                'name': player_ranking.name,
                'role': player_ranking.role,
                'evaluation': player_ranking.evaluation
            }
        
        # task_list를 딕셔너리로 변환 (이미 딕셔너리인 경우 처리)
        converted_task_list = {}
        for player_id, tasks in game_state.task_list.items():
            converted_task_list[player_id] = []
            for task in tasks:
                if isinstance(task, dict):
                    # 이미 딕셔너리인 경우 그대로 사용
                    converted_task_list[player_id].append(task)
                else:
                    # Pydantic 모델인 경우 변환
                    converted_task_list[player_id].append(convert_task_to_dict(task))
        
        # overtime_task_list를 딕셔너리로 변환 (이미 딕셔너리인 경우 처리)
        converted_overtime_task_list = {}
        for player_id, tasks in game_state.overtime_task_list.items():
            converted_overtime_task_list[player_id] = []
            for task in tasks:
                if isinstance(task, dict):
                    # 이미 딕셔너리인 경우 그대로 사용
                    converted_overtime_task_list[player_id].append(task)
                else:
                    # Pydantic 모델인 경우 변환
                    converted_overtime_task_list[player_id].append(convert_overtime_task_to_dict(task))
        
        # agenda_list를 딕셔너리로 변환 (이미 딕셔너리인 경우 처리)
        converted_agenda_list = []
        for agenda in game_state.agenda_list:
            if isinstance(agenda, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                converted_agenda_list.append(agenda)
            else:
                # Pydantic 모델인 경우 변환
                converted_agenda_list.append(convert_agenda_to_dict(agenda))
        
        # player_context_list를 딕셔너리로 변환 (이미 딕셔너리인 경우 처리)
        converted_player_context_list = []
        for pc in game_state.player_context_list:
            if isinstance(pc, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                converted_player_context_list.append(pc)
            else:
                # Pydantic 모델인 경우 변환
                converted_player_context_list.append(convert_player_context_to_dict(pc))
        
        # player_rankings를 딕셔너리로 변환 (이미 딕셔너리인 경우 처리)
        converted_player_rankings = []
        for pr in game_state.player_rankings:
            if isinstance(pr, dict):
                # 이미 딕셔너리인 경우 그대로 사용
                converted_player_rankings.append(pr)
            else:
                # Pydantic 모델인 경우 변환
                converted_player_rankings.append(convert_player_ranking_to_dict(pr))
        
        return {
            "room_id": room_id,
            "phase": game_state.phase.value if hasattr(game_state.phase, 'value') else str(game_state.phase),
            "current_turn": game_state.current_turn,
            "max_turn": game_state.max_turn,
            "story": game_state.story,
            "company_context": game_state.company_context,
            "player_context_list": converted_player_context_list,
            "agenda_list": converted_agenda_list,
            "task_list": converted_task_list,
            "overtime_task_list": converted_overtime_task_list,
            "explanation": game_state.explanation,
            "game_result": game_state.game_result,
            "player_rankings": converted_player_rankings,
            "created_at": game_state.created_at.isoformat() if game_state.created_at else None,
            "updated_at": game_state.updated_at.isoformat() if game_state.updated_at else None,
            "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
            "finished_at": game_state.finished_at.isoformat() if game_state.finished_at else None
        }

    # 아젠다 투표 관련 메서드들
    async def get_agenda_vote_status(self, room_id: str, agenda_id: str) -> Dict[str, Any]:
        """아젠다 투표 현황 조회"""
        from .agenda_vote_service import agenda_vote_service
        return await agenda_vote_service.get_vote_status(room_id, agenda_id)

    async def clear_agenda_votes(self, room_id: str, agenda_id: str) -> bool:
        """아젠다 투표 데이터 삭제"""
        from .agenda_vote_service import agenda_vote_service
        return await agenda_vote_service.clear_votes(room_id, agenda_id)

# 전역 게임 서비스 인스턴스
game_service = GameService() 
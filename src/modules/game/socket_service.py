import logging
from typing import Dict, Any, Optional, Set
from src.core.socket.models import BaseSocketMessage, SocketEventType
from src.modules.game.service import game_service
from datetime import datetime

logger = logging.getLogger(__name__)

# 투표 현황을 저장할 임시 저장소 (메모리 기반)
vote_storage: Dict[str, Dict[str, Dict[str, str]]] = {}  # room_id -> {agenda_id: {player_id: selected_option_id}}

# 태스크 완료 플레이어를 저장할 임시 저장소 (메모리 기반) - 개선된 구조
task_completed_players: Dict[str, Dict[str, Set[str]]] = {}  # room_id -> {player_id: set of completed task_ids}

# 태스크 생성 중복 방지 플래그
task_creation_in_progress: Set[str] = set()

class GameSocketService:
    """LLM 게임 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    def _get_player_task_count(room_id: str, player_id: str) -> int:
        """특정 플레이어의 총 태스크 수를 반환"""
        try:
            game_state = game_service.get_game_state(room_id)
            if not game_state or not hasattr(game_state, 'task_list'):
                return 0
            
            player_tasks = game_state.task_list.get(player_id, [])
            return len(player_tasks)
        except Exception as e:
            logger.error(f"플레이어 태스크 수 조회 실패: {e}")
            return 0
    
    @staticmethod
    def _is_player_all_tasks_completed(room_id: str, player_id: str) -> bool:
        """특정 플레이어의 모든 태스크가 완료되었는지 확인"""
        if room_id not in task_completed_players:
            return False
        
        if player_id not in task_completed_players[room_id]:
            return False
        
        completed_task_count = len(task_completed_players[room_id][player_id])
        total_task_count = GameSocketService._get_player_task_count(room_id, player_id)
        
        return completed_task_count >= total_task_count
    
    @staticmethod
    def _get_all_completed_players_count(room_id: str) -> int:
        """모든 태스크를 완료한 플레이어 수를 반환"""
        if room_id not in task_completed_players:
            return 0
        
        # 게임 상태에서 플레이어 목록을 가져와서 확인
        try:
            game_state = game_service.get_game_state(room_id)
            if not game_state or not hasattr(game_state, 'task_list'):
                return 0
            
            # task_list에 있는 모든 플레이어를 확인
            completed_count = 0
            for player_id in game_state.task_list.keys():
                if GameSocketService._is_player_all_tasks_completed(room_id, player_id):
                    completed_count += 1
            
            return completed_count
        except Exception as e:
            logger.error(f"완료된 플레이어 수 조회 실패: {e}")
            return 0
    
    @staticmethod
    async def handle_create_game(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """게임 생성 처리"""
        room_id = data.get('room_id')
        player_list = data.get('player_list', [])
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        if not player_list:
            await sio.emit('error', {'message': 'Player list is required.'}, room=sid)
            return None
        
        # 게임 시작 (스토리 생성)
        result = await game_service.start_game(room_id, player_list)
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        # 게임 시작 이벤트도 함께 전송 (프론트엔드 호환성)
        await sio.emit('start_game', {
            'room_id': room_id,
            'story': result.story
        }, room=room_id)
        
        logger.info(f"스토리 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_GAME,
            data={
                'room_id': room_id,
                'story': result.story,
                'phase': 'context_creation'
            }
        )
    
    @staticmethod
    async def handle_create_context(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """컨텍스트 생성 처리"""
        room_id = data.get('room_id')
        max_turn = data.get('max_turn', 10)
        story = data.get('story')  # story를 요청에서 받음
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        if not story:
            await sio.emit('error', {'message': 'Story is required.'}, room=sid)
            return None
        
        # 컨텍스트 생성 (story를 기반으로)
        result = await game_service.create_context(room_id, max_turn, story)
        
        # PlayerContext 객체를 딕셔너리로 변환
        def convert_player_context_to_dict(player_context):
            return {
                'id': player_context.id,
                'name': player_context.name,
                'role': player_context.role,
                'context': player_context.context
            }
        
        # player_context_list를 딕셔너리로 변환
        converted_player_context_list = [convert_player_context_to_dict(pc) for pc in result.player_context_list]
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        logger.info(f"컨텍스트 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_CONTEXT,
            data={
                'room_id': room_id,
                'company_context': result.company_context,
                'player_context_list': converted_player_context_list,
                'phase': 'agenda_creation'
            }
        )
    
    @staticmethod
    async def handle_create_agenda(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """아젠다 생성 처리"""
        room_id = data.get('room_id')
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 즉시 모든 플레이어에게 로딩 시작 알림
        await sio.emit(SocketEventType.AGENDA_LOADING_STARTED, {
            'room_id': room_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        # 아젠다 생성
        result = await game_service.create_agenda(room_id)
        
        # Agenda 객체를 딕셔너리로 변환
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
        
        # agenda_list를 딕셔너리로 변환
        converted_agenda_list = [convert_agenda_to_dict(agenda) for agenda in result.agenda_list]
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        logger.info(f"아젠다 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_AGENDA,
            data={
                'room_id': room_id,
                'description': result.description,
                'agenda_list': converted_agenda_list,
                'phase': 'task_creation'
            }
        )
    
    @staticmethod
    async def handle_vote_agenda(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """아젠다 투표 처리"""
        room_id = data.get('room_id')
        agenda_id = data.get('agenda_id')
        selected_option_id = data.get('selected_option_id')
        
        if not room_id or not agenda_id or not selected_option_id:
            await sio.emit('error', {'message': '필수 파라미터가 누락되었습니다.'}, room=sid)
            return None
        
        # 사용자 정보 가져오기
        user_id = session.get('user_id')
        player_name = data.get('player_name')  # 프론트엔드에서 전송한 플레이어 이름
        
        if not user_id:
            await sio.emit('error', {'message': '인증되지 않은 사용자입니다.'}, room=sid)
            return None
        
        # user_id로 프로필 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        if not profile:
            await sio.emit('error', {'message': '프로필을 찾을 수 없습니다.'}, room=sid)
            return None
        
        profile_id = profile.id
        
        # 투표 정보를 임시 저장소에 저장
        if room_id not in vote_storage:
            vote_storage[room_id] = {}
        
        if agenda_id not in vote_storage[room_id]:
            vote_storage[room_id][agenda_id] = {}
        
        vote_storage[room_id][agenda_id][profile_id] = selected_option_id
        
        # 투표 정보를 모든 플레이어에게 브로드캐스트
        vote_broadcast_data = {
            'room_id': room_id,
            'agenda_id': agenda_id,
            'player_id': profile_id,
            'player_name': player_name,
            'selected_option_id': selected_option_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await sio.emit(SocketEventType.AGENDA_VOTE_BROADCAST, vote_broadcast_data, room=room_id)
        
        logger.info(f"아젠다 투표 브로드캐스트: {room_id}, 플레이어: {player_name}")
        
        # 방 정보에서 총 플레이어 수 확인
        from src.modules.room.service import room_service
        room = await room_service.get_room(room_id)
        if not room:
            await sio.emit('error', {'message': '방을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 모든 플레이어가 투표했는지 확인
        total_players = len(room.players)
        voted_players = len(vote_storage[room_id][agenda_id])
        
        logger.info(f"투표 현황: {room_id}, agenda {agenda_id}, {voted_players}/{total_players} 플레이어 투표 완료")
        
        # 모든 플레이어가 투표 완료 시 결과 집계 및 브로드캐스트
        if voted_players >= total_players:
            # 투표 결과 집계
            vote_counts = {}
            for player_id, option_id in vote_storage[room_id][agenda_id].items():
                if option_id not in vote_counts:
                    vote_counts[option_id] = 0
                vote_counts[option_id] += 1
            
            # 가장 많이 투표된 옵션 찾기
            winning_option_id = max(vote_counts.items(), key=lambda x: x[1])[0]
            
            # 투표 완료 이벤트 브로드캐스트
            vote_completed_data = {
                'room_id': room_id,
                'agenda_id': agenda_id,
                'vote_results': vote_storage[room_id][agenda_id],
                'vote_counts': vote_counts,
                'winning_option_id': winning_option_id,
                'total_votes': total_players,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await sio.emit(SocketEventType.AGENDA_VOTE_COMPLETED, vote_completed_data, room=room_id)
            
            logger.info(f"투표 완료: {room_id}, agenda {agenda_id}, 승리 옵션: {winning_option_id}, 투표 결과: {vote_counts}")
            
            # 해당 agenda의 투표 저장소만 초기화 (다른 agenda는 유지)
            vote_storage[room_id][agenda_id] = {}
        
        return BaseSocketMessage(
            event_type=SocketEventType.AGENDA_VOTE_BROADCAST,
            data=vote_broadcast_data
        )
    
    @staticmethod
    async def handle_agenda_navigate(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """아젠다 네비게이션 처리 (다음/이전 안건으로 이동)"""
        room_id = data.get('room_id')
        action = data.get('action')  # 'next' 또는 'finish'
        
        if not room_id or not action:
            await sio.emit('error', {'message': '필수 파라미터가 누락되었습니다.'}, room=sid)
            return None
        
        # 사용자 정보 가져오기
        user_id = session.get('user_id')
        if not user_id:
            await sio.emit('error', {'message': '인증되지 않은 사용자입니다.'}, room=sid)
            return None
        
        # user_id로 프로필 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        if not profile:
            await sio.emit('error', {'message': '프로필을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 방 정보 확인
        from src.modules.room.service import room_service
        room = await room_service.get_room(room_id)
        if not room:
            await sio.emit('error', {'message': '방을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 호스트 권한 확인
        if room.host_profile_id != profile.id:
            await sio.emit('error', {'message': '호스트만 아젠다를 진행할 수 있습니다.'}, room=sid)
            return None
        
        # 모든 플레이어에게 아젠다 네비게이션 브로드캐스트
        navigate_data = {
            'room_id': room_id,
            'action': action,
            'host_profile_id': profile.id,
            'host_display_name': profile.display_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await sio.emit(SocketEventType.AGENDA_NAVIGATE, navigate_data, room=room_id)
        
        logger.info(f"아젠다 네비게이션 브로드캐스트: {room_id}, 액션: {action}, 호스트: {profile.display_name}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.AGENDA_NAVIGATE,
            data=navigate_data
        )
    
    @staticmethod
    async def handle_task_completed(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """태스크 완료 처리"""
        room_id = data.get('room_id')
        task_id = data.get('task_id')  # 완료된 태스크 ID
        
        if not room_id or not task_id:
            await sio.emit('error', {'message': 'Room ID와 Task ID가 필요합니다.'}, room=sid)
            return None
        
        # 사용자 정보 가져오기
        user_id = session.get('user_id')
        player_name = data.get('player_name')  # 프론트엔드에서 전송한 플레이어 이름
        
        if not user_id:
            await sio.emit('error', {'message': '인증되지 않은 사용자입니다.'}, room=sid)
            return None
        
        # user_id로 프로필 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        if not profile:
            await sio.emit('error', {'message': '프로필을 찾을 수 없습니다.'}, room=sid)
            return None
        
        profile_id = profile.id
        
        # 태스크 완료 플레이어를 저장소에 추가
        if room_id not in task_completed_players:
            task_completed_players[room_id] = {}
        
        if profile_id not in task_completed_players[room_id]:
            task_completed_players[room_id][profile_id] = set()
        
        # 해당 태스크를 완료 목록에 추가
        task_completed_players[room_id][profile_id].add(task_id)
        
        # 태스크 완료 정보를 모든 플레이어에게 브로드캐스트
        task_completed_data = {
            'room_id': room_id,
            'player_id': profile_id,
            'player_name': player_name,
            'task_id': task_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await sio.emit(SocketEventType.TASK_COMPLETED_BROADCAST, task_completed_data, room=room_id)
        
        logger.info(f"태스크 완료 브로드캐스트: {room_id}, 플레이어: {player_name}, 태스크: {task_id}")
        
        # 방 정보에서 총 플레이어 수 확인
        from src.modules.room.service import room_service
        room = await room_service.get_room(room_id)
        if not room:
            await sio.emit('error', {'message': '방을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 모든 플레이어가 태스크를 완료했는지 확인
        total_players = len(room.players)
        completed_players = GameSocketService._get_all_completed_players_count(room_id)
        
        logger.info(f"태스크 완료 현황: {room_id}, {completed_players}/{total_players} 플레이어 완료")
        
        return BaseSocketMessage(
            event_type=SocketEventType.TASK_COMPLETED_BROADCAST,
            data=task_completed_data
        )
    
    @staticmethod
    async def handle_task_navigate(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """태스크 네비게이션 처리 (다음 단계로 이동)"""
        room_id = data.get('room_id')
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 사용자 정보 가져오기
        user_id = session.get('user_id')
        if not user_id:
            await sio.emit('error', {'message': '인증되지 않은 사용자입니다.'}, room=sid)
            return None
        
        # user_id로 프로필 정보 조회
        from src.modules.profile.service import user_profile_service
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        if not profile:
            await sio.emit('error', {'message': '프로필을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 방 정보 확인
        from src.modules.room.service import room_service
        room = await room_service.get_room(room_id)
        if not room:
            await sio.emit('error', {'message': '방을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 호스트 권한 확인
        if room.host_profile_id != profile.id:
            await sio.emit('error', {'message': '호스트만 다음 단계로 진행할 수 있습니다.'}, room=sid)
            return None
        
        # 모든 플레이어가 태스크를 완료했는지 확인
        game_state = game_service.get_game_state(room_id)
        if not game_state or not hasattr(game_state, 'task_list'):
            await sio.emit('error', {'message': '게임 상태를 찾을 수 없습니다.'}, room=sid)
            return None
        
        total_players = len(game_state.task_list)
        completed_players = GameSocketService._get_all_completed_players_count(room_id)
        
        logger.info(f"태스크 완료 현황: {room_id}, {completed_players}/{total_players} 플레이어 완료")
        logger.info(f"게임 상태 task_list 플레이어: {list(game_state.task_list.keys())}")
        logger.info(f"완료된 태스크 저장소: {task_completed_players.get(room_id, {})}")
        
        if completed_players < total_players:
            await sio.emit('error', {'message': '모든 플레이어가 태스크를 완료해야 합니다.'}, room=sid)
            return None
        
        # 모든 플레이어에게 태스크 네비게이션 브로드캐스트
        navigate_data = {
            'room_id': room_id,
            'host_profile_id': profile.id,
            'host_display_name': profile.display_name,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await sio.emit(SocketEventType.TASK_NAVIGATE, navigate_data, room=room_id)
        
        # 태스크 완료 저장소 초기화
        if room_id in task_completed_players:
            task_completed_players[room_id].clear()
        
        logger.info(f"태스크 네비게이션 브로드캐스트: {room_id}, 호스트: {profile.display_name}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.TASK_NAVIGATE,
            data=navigate_data
        )
    
    @staticmethod
    async def handle_create_task(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """태스크 생성 처리"""
        room_id = data.get('room_id')
        
        logger.info(f"태스크 생성 요청 수신: {room_id}, 세션 ID: {sid}")
        
        # 중복 호출 방지
        if room_id in task_creation_in_progress:
            logger.warning(f"태스크 생성 중복 요청 무시: {room_id}")
            await sio.emit('error', {'message': '태스크 생성이 이미 진행 중입니다.'}, room=sid)
            return None
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 방 정보 확인
        from src.modules.room.service import room_service
        room = await room_service.get_room(room_id)
        if not room:
            await sio.emit('error', {'message': '방을 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 게임 상태 확인
        game_state = game_service.get_game_state(room_id)
        if not game_state:
            await sio.emit('error', {'message': '게임 상태를 찾을 수 없습니다.'}, room=sid)
            return None
        
        # 중복 호출 방지 플래그 설정
        task_creation_in_progress.add(room_id)
        
        # 게임 서비스를 통한 태스크 생성
        result = await game_service.create_task(room_id)
        
        # 태스크 생성 시에는 GAME_PROGRESS_UPDATED 이벤트를 보내지 않음
        # (프론트엔드에서 TASK_CREATED 이벤트로 처리)
        
        # Task 객체를 딕셔너리로 변환
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
        
        # task_list를 딕셔너리로 변환
        converted_task_list = {}
        for player_id, tasks in result.task_list.items():
            converted_task_list[player_id] = [convert_task_to_dict(task) for task in tasks]
        
        # 태스크 생성 완료 이벤트 전송
        task_data = {
            'room_id': room_id,
            'task_list': converted_task_list,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit(SocketEventType.TASK_CREATED, task_data, room=room_id)
        
        # 중복 호출 방지 플래그 제거
        task_creation_in_progress.discard(room_id)
        
        logger.info(f"태스크 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_TASK,
            data={
                'room_id': room_id,
                'task_list': converted_task_list,
                'phase': 'overtime_creation'
            }
        )
    
    @staticmethod
    async def handle_create_overtime(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """오버타임 생성 처리"""
        room_id = data.get('room_id')
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 오버타임 생성
        result = await game_service.create_overtime(room_id)
        
        # 오버타임 생성 시에는 GAME_PROGRESS_UPDATED 이벤트를 보내지 않음
        # (프론트엔드에서 OVERTIME_CREATED 이벤트로 처리)
        
        # OvertimeTask 객체를 딕셔너리로 변환
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
        
        # overtime_task_list를 딕셔너리로 변환
        converted_overtime_task_list = {}
        for player_id, tasks in result.task_list.items():
            converted_overtime_task_list[player_id] = [convert_overtime_task_to_dict(task) for task in tasks]
        
        # 오버타임 생성 완료 이벤트 전송
        overtime_data = {
            'room_id': room_id,
            'task_list': converted_overtime_task_list,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('overtime_created', overtime_data, room=room_id)
        
        logger.info(f"오버타임 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_OVERTIME,
            data={
                'room_id': room_id,
                'task_list': converted_overtime_task_list,
                'phase': 'playing'
            }
        )
    
    @staticmethod
    async def handle_update_context(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """컨텍스트 업데이트 처리"""
        room_id = data.get('room_id')
        agenda_selections = data.get('agenda_selections', {})
        task_selections = data.get('task_selections', {})
        overtime_selections = data.get('overtime_selections', {})
        
        logger.info(f"컨텍스트 업데이트 요청 수신: {room_id}")
        logger.info(f"아젠다 선택: {len(agenda_selections)}개")
        logger.info(f"태스크 선택: {len(task_selections)}개")
        logger.info(f"오버타임 선택: {len(overtime_selections)}개")
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 컨텍스트 업데이트
        result = await game_service.update_context(
            room_id, agenda_selections, task_selections, overtime_selections
        )
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        # PlayerContext 객체를 딕셔너리로 변환
        def convert_player_context_to_dict(player_context):
            return {
                'id': player_context.id,
                'name': player_context.name,
                'role': player_context.role,
                'context': player_context.context
            }
        
        # player_context_list를 딕셔너리로 변환
        converted_player_context_list = [convert_player_context_to_dict(pc) for pc in result.player_context_list]
        
        # 컨텍스트 업데이트 완료 이벤트 전송
        context_updated_data = {
            'room_id': room_id,
            'company_context': result.company_context,
            'player_context_list': converted_player_context_list,
            'phase': 'explanation',
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('context_updated', context_updated_data, room=room_id)
        
        logger.info(f"컨텍스트 업데이트 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.UPDATE_CONTEXT,
            data={
                'room_id': room_id,
                'company_context': result.company_context,
                'player_context_list': converted_player_context_list,
                'phase': 'explanation'
            }
        )
    
    @staticmethod
    async def handle_create_explanation(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """설명 생성 처리"""
        room_id = data.get('room_id')
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 설명 생성
        result = await game_service.create_explanation(room_id)
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        logger.info(f"설명 생성 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CREATE_EXPLANATION,
            data={
                'room_id': room_id,
                'explanation': result.explanation,
                'phase': 'result'
            }
        )
    
    @staticmethod
    async def handle_calculate_result(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """결과 계산 처리"""
        room_id = data.get('room_id')
        
        logger.info(f"결과 계산 요청 수신: {room_id}")
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 결과 계산
        result = await game_service.calculate_result(room_id)
        # ResultResponse를 딕셔너리로 변환
        result_dict = {
            'game_result': result.game_result,
            'player_rankings': result.player_rankings
        }
        
        # 방의 모든 사용자에게 게임 진행 상황 업데이트 알림
        game_progress = game_service.get_game_progress(room_id)
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, game_progress, room=room_id)
        
        # PlayerRanking 객체를 딕셔너리로 변환
        def convert_player_ranking_to_dict(player_ranking):
            return {
                'rank': player_ranking.rank,
                'id': player_ranking.id,
                'name': player_ranking.name,
                'role': player_ranking.role,
                'evaluation': player_ranking.evaluation
            }
        
        # player_rankings를 딕셔너리로 변환
        converted_player_rankings = [convert_player_ranking_to_dict(pr) for pr in result_dict['player_rankings']]
        
        # 게임 결과 생성 완료 이벤트 전송
        result_data = {
            'room_id': room_id,
            'game_result': result_dict['game_result'],
            'player_rankings': converted_player_rankings,
            'timestamp': datetime.utcnow().isoformat()
        }
        await sio.emit('game_result_created', result_data, room=room_id)
        
        logger.info(f"결과 계산 완료: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.CALCULATE_RESULT,
            data={
                'room_id': room_id,
                'game_result': result_dict['game_result'],
                'player_rankings': converted_player_rankings,
                'phase': 'finished'
            }
        )
    
    @staticmethod
    async def handle_get_game_progress(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """게임 진행 상황 조회 처리"""
        room_id = data.get('room_id')
        
        if not room_id:
            await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
            return None
        
        # 게임 진행 상황 조회
        progress = game_service.get_game_progress(room_id)
        
        # 방의 모든 사용자에게 게임 진행 상황 전송
        await sio.emit(SocketEventType.GAME_PROGRESS_UPDATED, progress, room=room_id)
        
        logger.info(f"게임 진행 상황 조회 성공: {room_id}")
        
        return BaseSocketMessage(
            event_type=SocketEventType.GET_GAME_PROGRESS,
            data=progress
        ) 
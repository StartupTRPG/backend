import logging
from typing import Dict, Any, Optional
from src.core.socket.models import BaseSocketMessage, SocketEventType
from src.modules.game.service import game_service

logger = logging.getLogger(__name__)

class GameSocketService:
    """LLM 게임 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_create_game(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """게임 생성 처리"""
        try:
            room_id = data.get('room_id')
            player_list = data.get('player_list', [])
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            if not player_list:
                await sio.emit('error', {'message': 'Player list is required.'}, room=sid)
                return None
            
            # 게임 시작
            result = await game_service.start_game(room_id, player_list)
            
            # 방의 모든 사용자에게 게임 생성 완료 알림
            await sio.emit('game_created', {
                'room_id': room_id,
                'story': result.story,
                'phase': 'context_creation'
            }, room=room_id)
            
            logger.info(f"게임 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_GAME,
                data={
                    'room_id': room_id,
                    'story': result.story,
                    'phase': 'context_creation'
                }
            )
            
        except Exception as e:
            logger.error(f"게임 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'게임 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_create_context(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """컨텍스트 생성 처리"""
        try:
            room_id = data.get('room_id')
            max_turn = data.get('max_turn', 10)
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 컨텍스트 생성
            result = await game_service.create_context(room_id, max_turn)
            
            # 방의 모든 사용자에게 컨텍스트 생성 완료 알림
            await sio.emit('context_created', {
                'room_id': room_id,
                'company_context': result.company_context,
                'player_context_list': result.player_context_list,
                'phase': 'agenda_creation'
            }, room=room_id)
            
            logger.info(f"컨텍스트 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_CONTEXT,
                data={
                    'room_id': room_id,
                    'company_context': result.company_context,
                    'player_context_list': result.player_context_list,
                    'phase': 'agenda_creation'
                }
            )
            
        except Exception as e:
            logger.error(f"컨텍스트 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'컨텍스트 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_create_agenda(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """아젠다 생성 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 아젠다 생성
            result = await game_service.create_agenda(room_id)
            
            # 방의 모든 사용자에게 아젠다 생성 완료 알림
            await sio.emit('agenda_created', {
                'room_id': room_id,
                'description': result.description,
                'agenda_list': result.agenda_list,
                'phase': 'task_creation'
            }, room=room_id)
            
            logger.info(f"아젠다 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_AGENDA,
                data={
                    'room_id': room_id,
                    'description': result.description,
                    'agenda_list': result.agenda_list,
                    'phase': 'task_creation'
                }
            )
            
        except Exception as e:
            logger.error(f"아젠다 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'아젠다 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_create_task(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """태스크 생성 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 태스크 생성
            result = await game_service.create_task(room_id)
            
            # 방의 모든 사용자에게 태스크 생성 완료 알림
            await sio.emit('task_created', {
                'room_id': room_id,
                'task_list': result.task_list,
                'phase': 'overtime_creation'
            }, room=room_id)
            
            logger.info(f"태스크 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_TASK,
                data={
                    'room_id': room_id,
                    'task_list': result.task_list,
                    'phase': 'overtime_creation'
                }
            )
            
        except Exception as e:
            logger.error(f"태스크 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'태스크 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_create_overtime(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """오버타임 생성 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 오버타임 생성
            result = await game_service.create_overtime(room_id)
            
            # 방의 모든 사용자에게 오버타임 생성 완료 알림
            await sio.emit('overtime_created', {
                'room_id': room_id,
                'task_list': result.task_list,
                'phase': 'playing'
            }, room=room_id)
            
            logger.info(f"오버타임 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_OVERTIME,
                data={
                    'room_id': room_id,
                    'task_list': result.task_list,
                    'phase': 'playing'
                }
            )
            
        except Exception as e:
            logger.error(f"오버타임 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'오버타임 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_update_context(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """컨텍스트 업데이트 처리"""
        try:
            room_id = data.get('room_id')
            agenda_selections = data.get('agenda_selections', {})
            task_selections = data.get('task_selections', {})
            overtime_selections = data.get('overtime_selections', {})
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 컨텍스트 업데이트
            result = await game_service.update_context(
                room_id, agenda_selections, task_selections, overtime_selections
            )
            
            # 방의 모든 사용자에게 컨텍스트 업데이트 완료 알림
            await sio.emit('context_updated', {
                'room_id': room_id,
                'company_context': result.company_context,
                'player_context_list': result.player_context_list,
                'phase': 'explanation'
            }, room=room_id)
            
            logger.info(f"컨텍스트 업데이트 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.UPDATE_CONTEXT,
                data={
                    'room_id': room_id,
                    'company_context': result.company_context,
                    'player_context_list': result.player_context_list,
                    'phase': 'explanation'
                }
            )
            
        except Exception as e:
            logger.error(f"컨텍스트 업데이트 실패: {str(e)}")
            await sio.emit('error', {'message': f'컨텍스트 업데이트 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_create_explanation(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """설명 생성 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 설명 생성
            result = await game_service.create_explanation(room_id)
            
            # 방의 모든 사용자에게 설명 생성 완료 알림
            await sio.emit('explanation_created', {
                'room_id': room_id,
                'explanation': result.explanation,
                'phase': 'result'
            }, room=room_id)
            
            logger.info(f"설명 생성 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CREATE_EXPLANATION,
                data={
                    'room_id': room_id,
                    'explanation': result.explanation,
                    'phase': 'result'
                }
            )
            
        except Exception as e:
            logger.error(f"설명 생성 실패: {str(e)}")
            await sio.emit('error', {'message': f'설명 생성 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_calculate_result(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """결과 계산 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 결과 계산
            result = await game_service.calculate_result(room_id)
            
            # 방의 모든 사용자에게 결과 계산 완료 알림
            await sio.emit('result_calculated', {
                'room_id': room_id,
                'game_result': result.game_result,
                'player_rankings': result.player_rankings,
                'phase': 'finished'
            }, room=room_id)
            
            logger.info(f"결과 계산 완료: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.CALCULATE_RESULT,
                data={
                    'room_id': room_id,
                    'game_result': result.game_result,
                    'player_rankings': result.player_rankings,
                    'phase': 'finished'
                }
            )
            
        except Exception as e:
            logger.error(f"결과 계산 실패: {str(e)}")
            await sio.emit('error', {'message': f'결과 계산 실패: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_get_game_progress(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """게임 진행 상황 조회 처리"""
        try:
            room_id = data.get('room_id')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 게임 진행 상황 조회
            progress = game_service.get_game_progress(room_id)
            
            # 요청한 사용자에게 게임 진행 상황 전송
            await sio.emit('game_progress', progress, room=sid)
            
            logger.info(f"게임 진행 상황 조회: {room_id}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.GET_GAME_PROGRESS,
                data=progress
            )
            
        except Exception as e:
            logger.error(f"게임 진행 상황 조회 실패: {str(e)}")
            await sio.emit('error', {'message': f'게임 진행 상황 조회 실패: {str(e)}'}, room=sid)
            return None 
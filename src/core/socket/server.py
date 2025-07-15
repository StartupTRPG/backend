import socketio
from fastapi import FastAPI
from typing import Dict, List
from datetime import datetime
import logging

from .handler import SocketMessageHandler
from .models.socket_event_type import SocketEventType

# 로깅 설정
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # 개발 환경에서는 모든 origin 허용
    logger=False,  # Socket.IO 로거 비활성화
    engineio_logger=False  # Engine.IO 로거 비활성화
)

# 연결된 프로필 관리 (전역 상태)
connected_profiles: Dict[str, Dict] = {}  # sid -> profile_info
room_profiles: Dict[str, List[str]] = {}  # room_id -> [sid1, sid2, ...]

# Socket.IO 앱 생성 함수
def create_socketio_app(fastapi_app: FastAPI) -> socketio.ASGIApp:
    """FastAPI 앱에 Socket.IO를 통합"""
    # 통합 메시지 핸들러 생성
    message_handler = SocketMessageHandler(sio)
    
    # 이벤트 핸들러 등록
    @sio.event
    async def connect(sid, environ, auth):
        """클라이언트 연결 이벤트"""
        try:
            await message_handler.handle_message(SocketEventType.CONNECT, sid, auth or {})
        except Exception as e:
            logger.error(f"Connect error: {str(e)}")
            raise socketio.exceptions.ConnectionRefusedError(str(e))
    
    @sio.event
    async def ping(sid, data):
        """클라이언트 핑 이벤트 - 세션 활동 업데이트"""
        try:
            from src.core.session_manager import session_manager
            await session_manager.update_session_activity(sid)
            await sio.emit('pong', {'timestamp': datetime.utcnow().isoformat()}, room=sid)
            
            # pong 전송 로깅 추가
            from .handler import log_socket_message
            log_socket_message('INFO', '전송', event='pong', sid=sid[:8])
        except Exception as e:
            logger.error(f"Ping error: {str(e)}")
    
    @sio.event
    async def disconnect(sid):
        """클라이언트 연결 해제 이벤트"""
        await message_handler.handle_message(SocketEventType.DISCONNECT, sid, {})
    
    @sio.event
    async def join_room(sid, data):
        """방 입장 이벤트"""
        await message_handler.handle_message(SocketEventType.JOIN_ROOM, sid, data)
    
    @sio.event
    async def leave_room(sid, data):
        """방 나가기 이벤트"""
        await message_handler.handle_message(SocketEventType.LEAVE_ROOM, sid, data)
    
    @sio.event
    async def ready(sid, data):
        """플레이어 레디/언레디 이벤트"""
        await message_handler.handle_message(SocketEventType.READY, sid, data)
    
    @sio.event
    async def start_game(sid, data):
        """게임 시작 이벤트"""
        await message_handler.handle_message(SocketEventType.START_GAME, sid, data)
    
    @sio.event
    async def finish_game(sid, data):
        """게임 종료 이벤트"""
        await message_handler.handle_message(SocketEventType.FINISH_GAME, sid, data)
    
    # LLM 게임 관련 이벤트 핸들러들
    @sio.event
    async def create_game(sid, data):
        """LLM 게임 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_GAME, sid, data)
    
    @sio.event
    async def create_context(sid, data):
        """컨텍스트 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_CONTEXT, sid, data)
    
    @sio.event
    async def create_agenda(sid, data):
        """아젠다 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_AGENDA, sid, data)
    
    @sio.event
    async def create_task(sid, data):
        """태스크 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_TASK, sid, data)
    
    @sio.event
    async def create_overtime(sid, data):
        """오버타임 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_OVERTIME, sid, data)
    
    @sio.event
    async def update_context(sid, data):
        """컨텍스트 업데이트 이벤트"""
        await message_handler.handle_message(SocketEventType.UPDATE_CONTEXT, sid, data)
    
    @sio.event
    async def create_explanation(sid, data):
        """설명 생성 이벤트"""
        await message_handler.handle_message(SocketEventType.CREATE_EXPLANATION, sid, data)
    
    @sio.event
    async def calculate_result(sid, data):
        """결과 계산 이벤트"""
        await message_handler.handle_message(SocketEventType.CALCULATE_RESULT, sid, data)
    
    @sio.event
    async def get_game_progress(sid, data):
        """게임 진행 상황 조회 이벤트"""
        await message_handler.handle_message(SocketEventType.GET_GAME_PROGRESS, sid, data)
    
    @sio.event
    async def send_message(sid, data):
        """채팅 메시지 전송 이벤트"""
        await message_handler.handle_message(SocketEventType.SEND_MESSAGE, sid, data)
    
    @sio.event
    async def get_chat_history(sid, data):
        """채팅 기록 조회 이벤트"""
        await message_handler.handle_message(SocketEventType.GET_CHAT_HISTORY, sid, data)
    
    @sio.event
    async def lobby_message(sid, data):
        """로비 메시지 이벤트"""
        await message_handler.handle_message(SocketEventType.LOBBY_MESSAGE, sid, data)
    
    @sio.event
    async def system_message(sid, data):
        """시스템 메시지 이벤트"""
        await message_handler.handle_message(SocketEventType.SYSTEM_MESSAGE, sid, data)
    
    @sio.event
    async def game_message(sid, data):
        """게임 메시지 이벤트"""
        await message_handler.handle_message(SocketEventType.GAME_MESSAGE, sid, data)
    
    # Socket.IO 앱을 FastAPI에 마운트
    socket_app = socketio.ASGIApp(sio, fastapi_app)
    
    # Socket.IO 엔드포인트 확인을 위한 로그
    logger.info("Socket.IO 앱이 FastAPI에 마운트되었습니다.")
    logger.info(f"Socket.IO 엔드포인트: /socket.io/")
    
    return socket_app

# 유틸리티 함수들
async def send_system_message(room_id: str, message: str) -> None:
    """시스템 메시지 전송"""
    from datetime import datetime
    await sio.emit('system_message', {
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'message_type': 'system'
    }, room=room_id)
    
    # 시스템 메시지 전송 로깅 추가
    from .handler import log_socket_message
    log_socket_message('INFO', '전송', event='system_message', room=room_id, msg=message[:30])

async def get_room_profile_count(room_id: str) -> int:
    """방의 현재 프로필 수 조회"""
    return len(room_profiles.get(room_id, []))

async def is_profile_in_room(profile_id: str, room_id: str) -> bool:
    """프로필이 특정 방에 있는지 확인"""
    for sid, profile_info in connected_profiles.items():
        if profile_info['profile_id'] == profile_id and profile_info['current_room'] == room_id:
            return True
    return False 
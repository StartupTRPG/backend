import socketio
from fastapi import FastAPI
from typing import Dict, List
from datetime import datetime
import logging

from .handler import SocketMessageHandler
from .interfaces import SocketEventType

# 로깅 설정
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # 개발 환경에서는 모든 origin 허용
    logger=True,
    engineio_logger=True
)

# 연결된 사용자 관리 (전역 상태)
connected_users: Dict[str, Dict] = {}  # sid -> user_info
room_users: Dict[str, List[str]] = {}  # room_id -> [sid1, sid2, ...]

# Socket.IO 앱 생성 함수
def create_socketio_app(fastapi_app: FastAPI):
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
    async def get_room_users(sid, data):
        """방 사용자 목록 조회 이벤트"""
        await message_handler.handle_message(SocketEventType.GET_ROOM_USERS, sid, data)
    
    @sio.event
    async def send_message(sid, data):
        """채팅 메시지 전송 이벤트"""
        await message_handler.handle_message(SocketEventType.SEND_MESSAGE, sid, data)
    
    @sio.event
    async def get_chat_history(sid, data):
        """채팅 기록 조회 이벤트"""
        await message_handler.handle_message(SocketEventType.GET_CHAT_HISTORY, sid, data)
    
    return socketio.ASGIApp(sio, fastapi_app)

# 유틸리티 함수들
async def send_system_message(room_id: str, message: str):
    """시스템 메시지 전송"""
    from datetime import datetime
    await sio.emit('system_message', {
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'message_type': 'system'
    }, room=room_id)

async def get_room_user_count(room_id: str) -> int:
    """방의 현재 사용자 수 조회"""
    return len(room_users.get(room_id, []))

async def is_user_in_room(user_id: str, room_id: str) -> bool:
    """사용자가 특정 방에 있는지 확인"""
    for sid, user_info in connected_users.items():
        if user_info['user_id'] == user_id and user_info['current_room'] == room_id:
            return True
    return False 
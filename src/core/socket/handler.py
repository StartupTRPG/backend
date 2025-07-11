from typing import Dict, Any, Optional, Callable
import logging
from .interfaces import (
    SocketEventType, BaseSocketMessage,
    AuthMessage, RoomMessage, ChatMessage, SystemMessage
)

logger = logging.getLogger(__name__)

class SocketMessageHandler:
    """통합 Socket 메시지 핸들러 - 공통 처리 및 라우팅"""
    
    def __init__(self, sio):
        self.sio = sio
        self.handlers: Dict[SocketEventType, Callable] = {}
        self._register_handlers()
    
    def _register_handlers(self):
        """핸들러 등록"""
        self.handlers = {
            SocketEventType.CONNECT: self._handle_connect,
            SocketEventType.DISCONNECT: self._handle_disconnect,
            SocketEventType.JOIN_ROOM: self._handle_join_room,
            SocketEventType.LEAVE_ROOM: self._handle_leave_room,
            SocketEventType.GET_ROOM_USERS: self._handle_get_room_users,
            SocketEventType.SEND_MESSAGE: self._handle_send_message,
            SocketEventType.GET_CHAT_HISTORY: self._handle_get_chat_history,
        }
    
    async def handle_message(self, event_type: SocketEventType, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """메시지 처리 - 공통 처리 및 라우팅"""
        try:
            handler = self.handlers.get(event_type)
            if not handler:
                logger.error(f"Unknown event type: {event_type}")
                await self._send_error(sid, f"알 수 없는 이벤트 타입: {event_type}")
                return None
            
            return await handler(sid, data)
            
        except Exception as e:
            logger.error(f"Message handling error for {event_type}: {str(e)}")
            await self._send_error(sid, "메시지 처리 중 오류가 발생했습니다.")
            return None
    
    async def _validate_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """세션 검증"""
        try:
            session = await self.sio.get_session(sid)
            if not session:
                await self._send_error(sid, "세션을 찾을 수 없습니다.")
                return None
            return session
        except Exception:
            await self._send_error(sid, "세션 검증 중 오류가 발생했습니다.")
            return None
    
    async def _send_error(self, sid: str, message: str):
        """에러 메시지 전송"""
        await self.sio.emit('error', {'message': message}, room=sid)
    
    async def _send_success(self, sid: str, data: Dict[str, Any]):
        """성공 메시지 전송"""
        await self.sio.emit('success', data, room=sid)
    
    # 인증 관련 핸들러 - 각 모듈 서비스로 위임
    async def _handle_connect(self, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 처리 - 인증 모듈로 위임"""
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_connect(self.sio, sid, data)
    
    async def _handle_disconnect(self, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 해제 처리 - 인증 모듈로 위임"""
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_disconnect(self.sio, sid, data)
    
    # 방 관련 핸들러 - 각 모듈 서비스로 위임
    async def _handle_join_room(self, sid: str, data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 입장 처리 - 방 모듈로 위임"""
        session = await self._validate_session(sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_join_room(self.sio, sid, session, data)
    
    async def _handle_leave_room(self, sid: str, data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 나가기 처리 - 방 모듈로 위임"""
        session = await self._validate_session(sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_leave_room(self.sio, sid, session, data)
    
    async def _handle_get_room_users(self, sid: str, data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 사용자 목록 조회 - 방 모듈로 위임"""
        session = await self._validate_session(sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_get_room_users(self.sio, sid, session, data)
    
    # 채팅 관련 핸들러 - 각 모듈 서비스로 위임
    async def _handle_send_message(self, sid: str, data: Dict[str, Any]) -> Optional[ChatMessage]:
        """메시지 전송 처리 - 채팅 모듈로 위임"""
        session = await self._validate_session(sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_send_message(self.sio, sid, session, data)
    
    async def _handle_get_chat_history(self, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """채팅 기록 조회 처리 - 채팅 모듈로 위임"""
        session = await self._validate_session(sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_get_chat_history(self.sio, sid, session, data) 
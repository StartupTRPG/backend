from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from .interfaces import BaseSocketMessage, SocketEventType
import socketio

logger = logging.getLogger(__name__)

class SocketMessageStrategy(ABC):
    """소켓 메시지 처리 전략 인터페이스"""
    
    @abstractmethod
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """메시지 처리 추상 메서드 - session 파라미터 제거"""
        pass
    
    @abstractmethod
    def get_event_type(self) -> SocketEventType:
        """이벤트 타입 반환"""
        pass
    
    async def _validate_session(self, sio: socketio.AsyncServer, sid: str) -> Optional[Dict[str, Any]]:
        """세션 검증 공통 메서드"""
        try:
            session = await sio.get_session(sid)
            if not session:
                await sio.emit('error', {'message': '세션을 찾을 수 없습니다.'}, room=sid)
                return None
            return session
        except Exception as e:
            logger.error(f"Session validation error for {sid}: {str(e)}")
            await sio.emit('error', {'message': '세션 검증 중 오류가 발생했습니다.'}, room=sid)
            return None

class AuthConnectStrategy(SocketMessageStrategy):
    """인증 연결 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 연결 시에는 세션 검증 불필요
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_connect(sio, sid, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.CONNECT

class AuthDisconnectStrategy(SocketMessageStrategy):
    """인증 연결 해제 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 연결 해제 시에는 세션 검증 불필요
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_disconnect(sio, sid, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.DISCONNECT

class RoomJoinStrategy(SocketMessageStrategy):
    """방 입장 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 세션 검증 필요
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_join_room(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.JOIN_ROOM

class RoomLeaveStrategy(SocketMessageStrategy):
    """방 나가기 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 세션 검증 필요
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_leave_room(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.LEAVE_ROOM

class RoomUsersStrategy(SocketMessageStrategy):
    """방 사용자 목록 조회 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 세션 검증 필요
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_get_room_users(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.GET_ROOM_USERS

class ChatSendMessageStrategy(SocketMessageStrategy):
    """채팅 메시지 전송 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 세션 검증 필요
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_send_message(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.SEND_MESSAGE

class ChatHistoryStrategy(SocketMessageStrategy):
    """채팅 기록 조회 처리 전략"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # 세션 검증 필요
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_get_chat_history(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.GET_CHAT_HISTORY 
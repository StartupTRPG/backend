from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from .interfaces import BaseSocketMessage, SocketEventType
import socketio

logger = logging.getLogger(__name__)

class SocketMessageStrategy(ABC):
    """Socket message strategy interface"""
    
    @abstractmethod
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """Message handling abstract method - session parameter removed"""
        pass
    
    @abstractmethod
    def get_event_type(self) -> SocketEventType:
        """Returns event type"""
        pass
    
    async def _validate_session(self, sio: socketio.AsyncServer, sid: str) -> Optional[Dict[str, Any]]:
        """Common session validation method"""
        try:
            session = await sio.get_session(sid)
            if not session:
                await sio.emit('error', {'message': 'Session not found.'}, room=sid)
                return None
            return session
        except Exception as e:
            logger.error(f"Session validation error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred during session validation.'}, room=sid)
            return None

class AuthConnectStrategy(SocketMessageStrategy):
    """Authentication connection handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Connection does not require session validation
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_connect(sio, sid, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.CONNECT

class AuthDisconnectStrategy(SocketMessageStrategy):
    """Authentication disconnection handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Disconnection does not require session validation
        from src.modules.auth.socket_service import AuthSocketService
        return await AuthSocketService.handle_disconnect(sio, sid, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.DISCONNECT

class RoomJoinStrategy(SocketMessageStrategy):
    """Room entry handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_join_room(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.JOIN_ROOM

class RoomLeaveStrategy(SocketMessageStrategy):
    """Room exit handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_leave_room(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.LEAVE_ROOM

class RoomUsersStrategy(SocketMessageStrategy):
    """Room user list query handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_get_room_users(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.GET_ROOM_USERS

class ChatSendMessageStrategy(SocketMessageStrategy):
    """Chat message sending handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_send_message(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.SEND_MESSAGE

class ChatHistoryStrategy(SocketMessageStrategy):
    """Chat history query handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.chat.socket_service import ChatSocketService
        return await ChatSocketService.handle_get_chat_history(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.GET_CHAT_HISTORY 
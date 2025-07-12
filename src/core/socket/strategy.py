from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from .interfaces import BaseSocketMessage
from .models.socket_event_type import SocketEventType
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



class LobbyMessageStrategy(SocketMessageStrategy):
    """Lobby message handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        try:
            room_id = data.get('room_id')
            message = data.get('message', '').strip()
            message_type = data.get('message_type', 'text')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            if not message:
                await sio.emit('error', {'message': 'Message content is required.'}, room=sid)
                return None
            
            if len(message) > 1000:
                await sio.emit('error', {'message': 'Message is too long. (Max 1000 characters)'}, room=sid)
                return None
            
            from datetime import datetime
            import time
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"lobby_{int(time.time() * 1000)}",
                'user_id': session['user_id'],
                'username': session['username'],
                'display_name': session.get('display_name', session['username']),
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'encrypted': False
            }
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('lobby_message', message_data, room=room_id)
            
            logger.info(f"Lobby message sent by {session['username']} in room {room_id}")
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="lobby_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'user_id': session['user_id'],
                    'username': session['username']
                }
            )
            
        except Exception as e:
            logger.error(f"Lobby message error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while sending the message.'}, room=sid)
            return None
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.LOBBY_MESSAGE

class GameMessageStrategy(SocketMessageStrategy):
    """Game message handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        try:
            room_id = data.get('room_id')
            message = data.get('message', '').strip()
            message_type = data.get('message_type', 'text')
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            if not message:
                await sio.emit('error', {'message': 'Message content is required.'}, room=sid)
                return None
            
            if len(message) > 1000:
                await sio.emit('error', {'message': 'Message is too long. (Max 1000 characters)'}, room=sid)
                return None
            
            from datetime import datetime
            import time
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"game_{int(time.time() * 1000)}",
                'user_id': session['user_id'],
                'username': session['username'],
                'display_name': session.get('display_name', session['username']),
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'encrypted': False
            }
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('game_message', message_data, room=room_id)
            
            logger.info(f"Game message sent by {session['username']} in room {room_id}")
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="game_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'user_id': session['user_id'],
                    'username': session['username']
                }
            )
            
        except Exception as e:
            logger.error(f"Game message error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while sending the message.'}, room=sid)
            return None
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.GAME_MESSAGE

class SystemMessageStrategy(SocketMessageStrategy):
    """System message handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        try:
            room_id = data.get('room_id')
            message = data.get('message', '').strip()
            message_type = data.get('message_type', 'system')
            metadata = data.get('metadata', {})
            
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            if not message:
                await sio.emit('error', {'message': 'Message content is required.'}, room=sid)
                return None
            
            from datetime import datetime
            import time
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"system_{int(time.time() * 1000)}",
                'user_id': 'system',
                'username': 'System',
                'display_name': 'System',
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'metadata': metadata,
                'encrypted': False
            }
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('system_message', message_data, room=room_id)
            
            logger.info(f"System message sent in room {room_id}: {message}")
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="system_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'metadata': metadata
                }
            )
            
        except Exception as e:
            logger.error(f"System message error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while sending the system message.'}, room=sid)
            return None
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.SYSTEM_MESSAGE 
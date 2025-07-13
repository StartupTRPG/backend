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

class StartGameStrategy(SocketMessageStrategy):
    """Game start handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_start_game(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.START_GAME

class FinishGameStrategy(SocketMessageStrategy):
    """Game finish handling strategy"""
    
    async def handle(self, sio: socketio.AsyncServer, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_finish_game(sio, sid, session, data)
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.FINISH_GAME

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
            
            # 디버깅을 위한 로깅 추가
            logger.info(f"LobbyMessageStrategy - room_id: {room_id}, message: {message[:20]}, user_id: {session.get('user_id')}")
            
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
            
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(session['user_id'])
            if not profile:
                logger.error(f"Profile not found for user_id: {session['user_id']}")
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None
            
            logger.info(f"Profile found: {profile.display_name} (ID: {profile.id})")
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"lobby_{int(time.time() * 1000)}",
                'profile_id': profile.id,
                'display_name': profile.display_name,
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'encrypted': False
            }

            # DB에 메시지 저장
            from src.modules.chat.service import chat_service
            from src.modules.chat.enums import ChatType
            
            logger.info(f"Saving message to DB - room_id: {room_id}, profile_id: {profile.id}, message: {message[:20]}")
            await chat_service.save_message(
                room_id=room_id,
                profile_id=profile.id,
                display_name=profile.display_name,
                message=message,
                message_type=ChatType.LOBBY
            )
            logger.info(f"Message saved successfully to DB")
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('lobby_message', message_data, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from .handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='lobby_message', room=room_id, profile=profile.display_name, msg=message[:30])
            
            logger.info(f"Lobby message sent by {profile.display_name} in room {room_id}")
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="lobby_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'profile_id': profile.id,
                    'display_name': profile.display_name
                }
            )
            
        except Exception as e:
            logger.error(f"Lobby message error for {sid}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(session['user_id'])
            if not profile:
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"game_{int(time.time() * 1000)}",
                'profile_id': profile.id,
                'display_name': profile.display_name,
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'encrypted': False
            }

            # DB에 메시지 저장
            from src.modules.chat.service import chat_service
            from src.modules.chat.enums import ChatType
            
            await chat_service.save_message(
                room_id=room_id,
                profile_id=profile.id,
                display_name=profile.display_name,
                message=message,
                message_type=ChatType.GAME
            )
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('game_message', message_data, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from .handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='game_message', room=room_id, profile=profile.display_name, msg=message[:30])
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="game_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'profile_id': profile.id,
                    'display_name': profile.display_name
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
            
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(session['user_id'])
            if not profile:
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None
            
            # 메시지 데이터 구성
            current_time = datetime.utcnow()
            message_data = {
                'id': f"system_{int(time.time() * 1000)}",
                'profile_id': profile.id,
                'display_name': profile.display_name,
                'message': message,
                'timestamp': current_time.isoformat(),
                'message_type': message_type,
                'encrypted': False
            }

            # DB에 메시지 저장
            from src.modules.chat.service import chat_service
            from src.modules.chat.enums import ChatType
            
            await chat_service.save_message(
                room_id=room_id,
                profile_id=profile.id,
                display_name=profile.display_name,
                message=message,
                message_type=ChatType.SYSTEM
            )
            
            # 해당 방의 모든 사용자에게 브로드캐스트
            await sio.emit('system_message', message_data, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from .handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='system_message', room=room_id, profile=profile.display_name, msg=message[:30])
            
            from .interfaces import BaseSocketMessage
            return BaseSocketMessage(
                event_type="system_message",
                data={
                    'room_id': room_id,
                    'message': message,
                    'profile_id': profile.id,
                    'display_name': profile.display_name
                }
            )
            
        except Exception as e:
            logger.error(f"System message error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while sending the message.'}, room=sid)
            return None
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.SYSTEM_MESSAGE

class ReadyStrategy(SocketMessageStrategy):
    """Ready status handling strategy"""
    
    def get_event_type(self) -> SocketEventType:
        return SocketEventType.READY
    
    async def handle(self, sio, sid, data):
        # Session validation required
        session = await self._validate_session(sio, sid)
        if not session:
            return None
        
        from src.modules.room.socket_service import RoomSocketService
        return await RoomSocketService.handle_ready(sio, sid, session, data) 
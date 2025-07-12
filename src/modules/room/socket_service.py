import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.models import RoomMessage, SocketEventType
from src.modules.room.service import room_service

logger = logging.getLogger(__name__)

class RoomSocketService:
    """방 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_join_room(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 입장 처리"""
        try:
            room_id = data.get('room_id')
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            password = data.get('password', '')
            
            # 방 존재 확인
            room = await room_service.get_room(room_id)
            if not room:
                await sio.emit('error', {'message': 'Room not found.'}, room=sid)
                return None
            
            # 비밀번호 확인
            if not room_service.verify_room_password(room, password):
                await sio.emit('error', {'message': 'Incorrect password.'}, room=sid)
                return None
            
            # 방 최대 인원 확인 (새로운 Room 모델 구조 사용)
            if room.current_players >= room.max_players:
                await sio.emit('error', {'message': 'Room is full.'}, room=sid)
                return None
            
            # 세션 매니저를 통한 방 입장 (여러 방 접속 방지)
            from src.core.session_manager import session_manager
            room_joined = await session_manager.join_room(sid, user_id, room_id)
            if not room_joined:
                await sio.emit('error', {'message': 'Failed to join room.'}, room=sid)
                return None
            
            # 이미 다른 방에 있다면 나가기 (기존 로직 유지)
            current_room = session.get('current_room')
            if current_room and current_room != room_id:
                await RoomSocketService.handle_leave_room_internal(sio, sid, current_room)
            
            # 방 입장 처리
            user_id = session['user_id']
            username = session['username']
            
            # 데이터베이스에 플레이어 추가
            success = await room_service.add_player_to_room(room_id, user_id, username, password)
            if not success:
                await sio.emit('error', {'message': 'Failed to join room.'}, room=sid)
                return None
            
            # Socket.IO 방에 입장
            await sio.enter_room(sid, room_id)
            
            # 세션 업데이트
            session['current_room'] = room_id
            await sio.save_session(sid, session)
            
            # 방 사용자 목록 업데이트 (기존 로직 유지)
            from src.core.socket.server import room_users, connected_users
            if room_id not in room_users:
                room_users[room_id] = []
            room_users[room_id].append(sid)
            
            # 연결된 사용자 정보 업데이트
            if sid in connected_users:
                connected_users[sid]['current_room'] = room_id
            
            # 기존 토큰에 방 정보 추가
            from src.core.jwt_utils import jwt_manager
            current_token = session.get('access_token')
            updated_token = None
            
            if current_token:
                updated_token = jwt_manager.update_token_with_room_info(
                    token=current_token,
                    room_id=room_id,
                    room_permissions="write"
                )
                
                # 세션에 업데이트된 토큰 저장
                session['access_token'] = updated_token
                await sio.save_session(sid, session)
            
            # 방 입장 성공 응답 (업데이트된 토큰 포함)
            await sio.emit('room_joined', {
                'room_id': room_id,
                'room_name': room.title,
                'updated_token': updated_token,
                'message': f'Joined {room.title}.'
            }, room=sid)
            
            # 시스템 메시지 저장 및 전송
            await RoomSocketService._send_system_message(sio, room_id, f'{username} has joined.')
            
            # 다른 사용자들에게 입장 알림
            await sio.emit('user_joined', {
                'user_id': user_id,
                'username': username,
                'display_name': session.get('display_name', username),
                'message': f'{username} has joined.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id, skip_sid=sid)
            
            logger.info(f"User {username} joined room {room_id}")
            
            return RoomMessage(
                event_type=SocketEventType.JOIN_ROOM,
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username'],
                password=password
            )
            
        except Exception as e:
            logger.error(f"Join room error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while joining the room.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_leave_room(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 나가기 처리"""
        try:
            room_id = data.get('room_id') or session.get('current_room')
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            await RoomSocketService.handle_leave_room_internal(sio, sid, room_id)
            
            return RoomMessage(
                event_type=SocketEventType.LEAVE_ROOM,
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username']
            )
            
        except Exception as e:
            logger.error(f"Leave room error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while leaving the room.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_get_room_users(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 사용자 목록 조회"""
        try:
            room_id = data.get('room_id') or session.get('current_room')
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 데이터베이스에서 방 사용자 목록 조회
            players = await room_service.get_room_players(room_id)
            
            # 사용자 정보 구성
            users = []
            for player in players:
                user_info = {
                    'user_id': player.user_id,
                    'username': player.username,
                    'display_name': player.username,  # 프로필 정보가 있다면 사용
                    'is_host': player.is_host,
                    'joined_at': player.joined_at.isoformat()
                }
                users.append(user_info)
            
            await sio.emit('room_users', {
                'room_id': room_id,
                'users': users,
                'total_count': len(users)
            }, room=sid)
            
            logger.info(f"Room users retrieved for room {room_id}")
            
            return RoomMessage(
                event_type=SocketEventType.GET_ROOM_USERS,
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username']
            )
            
        except Exception as e:
            logger.error(f"Get room users error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while retrieving room users.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_leave_room_internal(sio, sid: str, room_id: str):
        """내부 방 나가기 처리"""
        try:
            session = await sio.get_session(sid)
            if not session:
                return
            
            user_id = session['user_id']
            username = session['username']
            
            # 데이터베이스에서 플레이어 제거
            await room_service.remove_player_from_room(room_id, user_id)
            
            # Socket.IO 방에서 나가기
            await sio.leave_room(sid, room_id)
            
            # 세션 업데이트 (토큰에서 방 정보 제거)
            session['current_room'] = None
            
            # 토큰에서 방 정보 제거
            from src.core.jwt_utils import jwt_manager
            current_token = session.get('access_token')
            if current_token:
                updated_token = jwt_manager.remove_room_info_from_token(current_token)
                session['access_token'] = updated_token
            
            await sio.save_session(sid, session)
            
            # 세션 매니저에서 방 나가기
            from src.core.session_manager import session_manager
            await session_manager.leave_room(sid, user_id)
            
            # 방 사용자 목록 업데이트 (기존 로직 유지)
            from src.core.socket.server import room_users, connected_users
            if room_id in room_users and sid in room_users[room_id]:
                room_users[room_id].remove(sid)
                if not room_users[room_id]:
                    del room_users[room_id]
            
            # 연결된 사용자 정보 업데이트
            if sid in connected_users:
                connected_users[sid]['current_room'] = None
            
            # 방 나가기 성공 응답
            await sio.emit('room_left', {
                'room_id': room_id,
                'message': 'You have left the room.'
            }, room=sid)
            
            # 시스템 메시지 저장 및 전송
            await RoomSocketService._send_system_message(sio, room_id, f'{username} has left.')
            
            # 다른 사용자들에게 퇴장 알림
            await sio.emit('user_left', {
                'user_id': user_id,
                'username': username,
                'display_name': session.get('display_name', username),
                'message': f'{username} has left.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
            
            logger.info(f"User {username} left room {room_id}")
            
        except Exception as e:
            logger.error(f"Leave room internal error: {str(e)}")
    
    @staticmethod
    async def _send_system_message(sio, room_id: str, content: str):
        """시스템 메시지 전송"""
        from src.modules.chat.service import chat_service
        
        # 시스템 메시지는 암호화하지 않음
        system_message = await chat_service.save_system_message(room_id, content)
        
        # 시스템 메시지를 채팅으로 전송
        await sio.emit('new_message', {
            'id': system_message.id,
            'user_id': 'system',
            'username': 'System',
            'display_name': 'System',
            'message': system_message.content,
            'timestamp': system_message.timestamp.isoformat(),
            'message_type': 'system',
            'encrypted': False
        }, room=room_id) 
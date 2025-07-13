import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.models import RoomMessage, SocketEventType
from src.modules.room.service import room_service
from src.modules.room.enums import PlayerRole

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
            
            # 방 존재 확인
            room = await room_service.get_room(room_id)
            if not room:
                await sio.emit('error', {'message': 'Room not found.'}, room=sid)
                return None
            
            # 방 최대 인원 확인 (새로운 Room 모델 구조 사용)
            if room.current_players >= room.max_players:
                await sio.emit('error', {'message': 'Room is full.'}, room=sid)
                return None
            
            # 게임 진행 중인지 확인
            if room.status == 'playing':
                await sio.emit('error', {'message': 'Cannot join room while game is in progress.'}, room=sid)
                return None
            
            # 방 입장 처리
            user_id = session['user_id']
            username = session['username']
            
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
            
            # 데이터베이스에 플레이어 추가
            success = await room_service.add_player_to_room(room_id, user_id, username)
            if not success:
                await sio.emit('error', {'message': 'Failed to join room.'}, room=sid)
                return None
            
            # Socket.IO 방에 입장
            await sio.enter_room(sid, room_id)
            await sio.emit('join_room', {
                'room_id': room_id,
                'user_id': user_id,
                'username': username,
                'display_name': session.get('display_name', username),
                'message': f'{username} has joined.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
            
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
            

            
            logger.info(f"User {username} joined room {room_id}")
            
            return RoomMessage(
                event_type=SocketEventType.JOIN_ROOM,
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username']
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
    async def handle_leave_room_internal(sio, sid: str, room_id: str):
        """내부 방 나가기 처리"""
        try:
            session = await sio.get_session(sid)
            if not session:
                return
            
            user_id = session['user_id']
            username = session['username']
            
            # 데이터베이스에서 플레이어 제거 (호스트인 경우 방 삭제)
            is_host = False
            # Room 모델을 직접 조회하여 get_player 메서드 사용
            from src.modules.room.repository import get_room_repository
            room_repo = get_room_repository()
            room = await room_repo.find_by_id(room_id)
            if room:
                player = room.get_player(user_id)
                if player and player.role == PlayerRole.HOST:
                    is_host = True
            
            await room_service.remove_player_from_room(room_id, user_id)
            
            # 호스트가 나가는 경우 방 삭제 알림
            if is_host:
                await sio.emit('room_deleted', {
                    'room_id': room_id,
                    'message': f'Room has been deleted by host {username}.',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
            else:
                # 일반 사용자 나가기
                await sio.emit('leave_room', {
                    'room_id': room_id,
                    'user_id': user_id,
                    'username': username,
                    'display_name': session.get('display_name', username),
                    'message': f'{username} has left.',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
            
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
            

            
            logger.info(f"User {username} left room {room_id}")
            
        except Exception as e:
            logger.error(f"Leave room internal error: {str(e)}")
    
 
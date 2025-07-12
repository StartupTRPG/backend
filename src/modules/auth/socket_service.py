import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.interfaces import AuthMessage, SocketEventType
from src.modules.user.service import user_service

logger = logging.getLogger(__name__)

class AuthSocketService:
    """인증 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_connect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 처리"""
        try:
            # JWT 토큰 검증
            from src.core.jwt_utils import jwt_manager
            token = data.get('token')
            if not token:
                logger.warning(f"Connection rejected for {sid}: No token provided")
                raise Exception('Authentication required')
            
            payload = jwt_manager.verify_token(token)
            if not payload or payload.get("type") != "access":
                logger.warning(f"Connection rejected for {sid}: Invalid token")
                raise Exception('Invalid token')
            
            # 사용자 정보 조회
            user = await user_service.get_user_by_id(payload["user_id"])
            if not user:
                logger.warning(f"Connection rejected for {sid}: User not found")
                raise Exception('User not found')
            
            # 연결된 사용자 정보 저장
            from src.core.socket.server import connected_users
            connected_users[sid] = {
                'user_id': user.id,
                'username': user.username,
                'display_name': user.username,
                'current_room': None,
                'connected_at': datetime.utcnow()
            }
            
            # 사용자 세션 저장 (토큰 포함)
            session_data = connected_users[sid].copy()
            session_data['access_token'] = token  # 토큰을 세션에 저장
            await sio.save_session(sid, session_data)
            
            logger.info(f"User {user.username} connected with sid {sid}")
            
            # 연결 성공 응답
            await sio.emit('connect_success', {
                'user_id': user.id,
                'username': user.username,
                'message': '성공적으로 연결되었습니다.'
            }, room=sid)
            
            return AuthMessage(
                event_type=SocketEventType.CONNECT,
                token=token,
                user_id=user.id,
                username=user.username
            )
            
        except Exception as e:
            logger.error(f"Connection error for {sid}: {str(e)}")
            raise Exception('Connection failed')
    
    @staticmethod
    async def handle_disconnect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 해제 처리"""
        try:
            session = await sio.get_session(sid)
            if session:
                user_id = session.get('user_id')
                username = session.get('username')
                current_room = session.get('current_room')
                
                # 방에서 나가기 처리
                if current_room:
                    from src.modules.room.socket_service import RoomSocketService
                    await RoomSocketService.handle_leave_room_internal(sio, sid, current_room)
                
                # 연결된 사용자 목록에서 제거
                from src.core.socket.server import connected_users
                if sid in connected_users:
                    del connected_users[sid]
                
                logger.info(f"User {username} disconnected (sid: {sid})")
                
                return AuthMessage(
                    event_type=SocketEventType.DISCONNECT,
                    user_id=user_id,
                    username=username
                )
            
        except Exception as e:
            logger.error(f"Disconnect error for {sid}: {str(e)}")
        
        return None 
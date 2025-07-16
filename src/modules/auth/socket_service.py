import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.models import AuthMessage, SocketEventType

logger = logging.getLogger(__name__)

class AuthSocketService:
    """인증 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_connect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 처리"""
        from src.core.jwt_utils import jwt_manager
        
        # 이미 연결된 세션이 있는지 확인
        existing_session = await sio.get_session(sid)
        if existing_session:
            logger.info(f"Session already exists for {sid}, ignoring duplicate connect")
            return AuthMessage(
                event_type=SocketEventType.CONNECT,
                token=existing_session.get('access_token'),
                user_id=existing_session.get('user_id'),
                username=existing_session.get('username')
            )
        
        # token 또는 access_token 파라미터 처리
        token = data.get('token') or data.get('access_token')
        if not token:
            logger.warning(f"No token provided for connection {sid}")
            await sio.emit('connect_failed', {'message': 'Token is required.'}, room=sid)
            await sio.disconnect(sid)
            return None
        
        logger.info(f"Verifying token for connection {sid}")
        payload = jwt_manager.verify_token(token)
        if not payload:
            logger.warning(f"Token verification failed for {sid} - token is invalid or expired")
            await sio.emit('connect_failed', {'message': 'Invalid or expired token.'}, room=sid)
            await sio.disconnect(sid)
            return None
        
        if payload.get("type") != "access":
            logger.warning(f"Wrong token type for {sid}: {payload.get('type')}")
            await sio.emit('connect_failed', {'message': 'Invalid token type.'}, room=sid)
            await sio.disconnect(sid)
            return None
        
        # 세션에 사용자 정보 저장
        session = {
            'user_id': payload["user_id"],
            'username': payload.get("username", ""),
            'access_token': token,
            'connected_at': datetime.utcnow().isoformat()
        }
        await sio.save_session(sid, session)
        
        # 연결 성공 응답
        await sio.emit('connect_success', {
            'user_id': payload["user_id"],
            'username': payload.get("username", ""),
            'message': 'Connected successfully.'
        }, room=sid)
        
        return AuthMessage(
            event_type=SocketEventType.CONNECT,
            token=token,
            user_id=payload["user_id"],
            username=payload.get("username", "")
        )
    
    @staticmethod
    async def handle_disconnect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 해제 처리"""
        # 연결 해제 시 별도 세션/connected_profiles 관리 없음
        return None 
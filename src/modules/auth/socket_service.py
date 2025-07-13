import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.models import AuthMessage, SocketEventType
from src.modules.user.service import user_service

logger = logging.getLogger(__name__)

class AuthSocketService:
    """인증 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_connect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 처리"""
        try:
            from src.core.jwt_utils import jwt_manager
            token = data.get('token')
            if not token:
                await sio.emit('connect_failed', {'message': 'Token is required.'}, room=sid)
                await sio.disconnect(sid)
                return None
            
            payload = jwt_manager.verify_token(token)
            if not payload or payload.get("type") != "access":
                await sio.emit('connect_failed', {'message': 'Invalid token.'}, room=sid)
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
            
        except Exception as e:
            logger.error(f"Connection error for {sid}: {str(e)}")
            await sio.emit('connect_failed', {'message': 'Authentication failed.'}, room=sid)
            await sio.disconnect(sid)
            return None
    
    @staticmethod
    async def handle_disconnect(sio, sid: str, data: Dict[str, Any]) -> Optional[AuthMessage]:
        """연결 해제 처리"""
        try:
            # 연결 해제 시 별도 세션/connected_profiles 관리 없음
            return None
            
        except Exception as e:
            logger.error(f"Disconnect error for {sid}: {str(e)}")
        
        return None 
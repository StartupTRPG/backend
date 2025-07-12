import logging
from typing import Dict, Any, Optional
from src.core.socket.models import ChatMessage, BaseSocketMessage, SocketEventType
from src.core.encryption import encryption_service
from src.modules.chat.service import chat_service
from src.modules.chat.enum import ChatType

logger = logging.getLogger(__name__)

class ChatSocketService:
    """채팅 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_send_message(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[ChatMessage]:
        """채팅 메시지 전송 처리"""
        try:
            # 토큰에서 방 정보 확인
            from src.core.jwt_utils import jwt_manager
            current_token = session.get('access_token')
            
            if not current_token:
                await sio.emit('error', {'message': '토큰이 필요합니다.'}, room=sid)
                return None
            
            room_info = jwt_manager.get_room_info_from_token(current_token)
            if not room_info:
                await sio.emit('error', {'message': '방 정보가 없습니다.'}, room=sid)
                return None
            
            room_id = room_info['room_id']
            permissions = room_info['room_permissions']
            
            # 권한 확인
            if permissions == "read":
                await sio.emit('error', {'message': '읽기 전용 권한입니다.'}, room=sid)
                return None
            
            # 방 ID 확인
            if not room_id:
                await sio.emit('error', {'message': '방 ID가 필요합니다.'}, room=sid)
                return None
            
            # 메시지 검증 및 처리...
            message = data.get('message', '').strip()
            if not message:
                await sio.emit('error', {'message': '메시지 내용이 필요합니다.'}, room=sid)
                return None
            
            if len(message) > 1000:
                await sio.emit('error', {'message': '메시지가 너무 깁니다. (최대 1000자)'}, room=sid)
                return None
            
            # 메시지 암호화
            encrypted_message = encryption_service.encrypt_message(message)
            
            # 메시지를 데이터베이스에 저장 (암호화된 상태로)
            saved_message = await chat_service.save_message(
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username'],
                display_name=session.get('display_name', session['username']),
                content=encrypted_message,
                message_type=ChatType.TEXT
            )
            
            # 실시간 전송용 메시지 (복호화된 상태로)
            message_data = {
                'id': saved_message.id,
                'user_id': saved_message.user_id,
                'username': saved_message.username,
                'display_name': saved_message.display_name,
                'message': message,  # 원본 메시지 전송
                'timestamp': saved_message.timestamp.isoformat(),
                'message_type': saved_message.message_type,
                'encrypted': True
            }
            
            # 방의 모든 사용자에게 메시지 전송
            await sio.emit('new_message', message_data, room=room_id)
            
            logger.info(f"Encrypted message sent by {session['username']} in room {room_id}")
            
            return ChatMessage(
                event_type=SocketEventType.SEND_MESSAGE,
                room_id=room_id,
                user_id=session['user_id'],
                username=session['username'],
                display_name=session.get('display_name', session['username']),
                message=message,
                message_type="text",
                encrypted=True
            )
            
        except Exception as e:
            logger.error(f"Send message error for {sid}: {str(e)}")
            await sio.emit('error', {'message': '메시지 전송 중 오류가 발생했습니다.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_get_chat_history(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """채팅 기록 조회 처리"""
        try:
            room_id = data.get('room_id')
            if not room_id:
                await sio.emit('error', {'message': '방 ID가 필요합니다.'}, room=sid)
                return None
            
            page = data.get('page', 1)
            limit = data.get('limit', 50)
            
            # 채팅 기록 조회
            chat_history = await chat_service.get_room_messages(room_id, page, limit)
            
            # 메시지 데이터 변환 및 복호화
            messages = []
            for msg in chat_history.messages:
                # 메시지 복호화
                decrypted_content = msg.content
                if msg.message_type == ChatType.TEXT:
                    decrypted_content = encryption_service.decrypt_message(msg.content)
                
                messages.append({
                    'id': msg.id,
                    'user_id': msg.user_id,
                    'username': msg.username,
                    'display_name': msg.display_name,
                    'message': decrypted_content,
                    'timestamp': msg.timestamp.isoformat(),
                    'message_type': msg.message_type,
                    'encrypted': msg.message_type == ChatType.TEXT
                })
            
            # 채팅 기록 응답
            await sio.emit('chat_history', {
                'room_id': room_id,
                'messages': messages,
                'total_count': chat_history.total_count,
                'page': chat_history.page,
                'limit': chat_history.limit
            }, room=sid)
            
            logger.info(f"Chat history retrieved for room {room_id} by {session['username']}")
            
            return BaseSocketMessage(
                event_type=SocketEventType.GET_CHAT_HISTORY,
                data={
                    'room_id': room_id,
                    'message_count': len(messages)
                }
            )
            
        except Exception as e:
            logger.error(f"Get chat history error for {sid}: {str(e)}")
            await sio.emit('error', {'message': '채팅 기록 조회 중 오류가 발생했습니다.'}, room=sid)
            return None 
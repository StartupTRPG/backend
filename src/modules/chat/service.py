from datetime import datetime
from typing import List, Optional
import logging
from src.modules.chat.models import ChatMessage
from src.modules.chat.enum import ChatType
from src.modules.chat.dto import ChatMessageResponse, RoomChatHistoryResponse
from src.modules.chat.repository import get_chat_repository, ChatRepository

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, chat_repository: ChatRepository = None):
        self.chat_repository = chat_repository or get_chat_repository()
    
    async def save_message(
        self, 
        room_id: str, 
        user_id: str, 
        username: str, 
        display_name: str, 
        content: str, 
        message_type: ChatType = ChatType.LOBBY
    ) -> ChatMessageResponse:
        """Save chat message"""
        try:
            logger.info(f"Saving message in room {room_id} by user {username}")
            # room_id를 문자열로 저장
            from bson import ObjectId
            try:
                # ObjectId로 변환 시도 후 문자열로 저장
                object_id = ObjectId(room_id)
                room_id_str = str(object_id)
            except:
                # 이미 문자열이면 그대로 사용
                room_id_str = room_id
            
            message = ChatMessage(
                id=None,
                room_id=room_id_str,
                user_id=user_id,
                username=username,
                display_name=display_name,
                message_type=message_type,
                content=content,
                timestamp=datetime.utcnow()
            )
            message_id = await self.chat_repository.create(message)
            message.id = message_id
            return ChatMessageResponse(
                id=message.id,
                room_id=message.room_id,
                user_id=user_id,
                username=message.username,
                display_name=message.display_name,
                message_type=message.message_type,
                message=message.content,
                timestamp=message.timestamp
            )
        except Exception as e:
            logger.error(f"Error saving message in room {room_id}: {str(e)}")
            raise
    
    async def get_room_messages(
        self, 
        room_id: str, 
        page: int = 1, 
        limit: int = 50
    ) -> RoomChatHistoryResponse:
        """Get room chat messages (with pagination)"""
        try:
            logger.info(f"Fetching messages for room {room_id} (page: {page}, limit: {limit})")
            skip = (page - 1) * limit
            messages = await self.chat_repository.find_by_room_id(room_id, skip, limit)
            # 시간순 정렬 (오래된 것부터)
            messages = sorted(messages, key=lambda m: m.timestamp)
            # 총 메시지 수 조회
            total_count = await self.chat_repository.count({"room_id": room_id})
            return RoomChatHistoryResponse(
                room_id=room_id,
                messages=[ChatMessageResponse(
                    id=m.id,
                    room_id=m.room_id,
                    user_id=getattr(m, 'user_id', m.username),  # 기존 메시지는 username을 user_id로 사용
                    username=m.username,
                    display_name=m.display_name,
                    message_type=m.message_type,
                    message=m.content,
                    timestamp=m.timestamp
                ) for m in messages],
                total_count=total_count,
                page=page,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error fetching messages for room {room_id}: {str(e)}")
            raise
    
    async def delete_room_messages(self, room_id: str) -> int:
        try:
            logger.warning(f"Deleting all messages for room {room_id}")
            # MongoRepository's delete_many needs direct implementation. Temporarily pass
            # result = await self.chat_repository.delete_many({"room_id": room_id})
            # return result.deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error deleting messages for room {room_id}: {str(e)}")
            raise

    async def create_test_messages(self, room_id: str) -> List[ChatMessageResponse]:
        """테스트용 더미 메시지 생성"""
        try:
            # room_id를 문자열로 저장
            from bson import ObjectId
            try:
                # ObjectId로 변환 시도 후 문자열로 저장
                object_id = ObjectId(room_id)
                room_id_str = str(object_id)
            except:
                # 이미 문자열이면 그대로 사용
                room_id_str = room_id
            
            test_messages = [
                {
                    "user_id": "test_user_1",
                    "username": "startup_master",
                    "display_name": "스타트업 마스터",
                    "content": "안녕하세요! 스타트업 TRPG에 오신 것을 환영합니다!",
                    "message_type": ChatType.LOBBY
                },
                {
                    "user_id": "test_user_2", 
                    "username": "tech_enthusiast",
                    "display_name": "기술 애호가",
                    "content": "안녕하세요! 기대됩니다!",
                    "message_type": ChatType.LOBBY
                },
                {
                    "user_id": "test_user_3",
                    "username": "business_guru", 
                    "display_name": "비즈니스 구루",
                    "content": "창업 아이디어를 구상해보죠!",
                    "message_type": ChatType.LOBBY
                }
            ]
            
            saved_messages = []
            for msg_data in test_messages:
                message = ChatMessage(
                    id=None,
                    room_id=room_id_str,
                    user_id=msg_data["user_id"],
                    username=msg_data["username"],
                    display_name=msg_data["display_name"],
                    message_type=msg_data["message_type"],
                    content=msg_data["content"],
                    timestamp=datetime.utcnow()
                )
                message_id = await self.chat_repository.create(message)
                message.id = message_id
                saved_messages.append(ChatMessageResponse(
                    id=message.id,
                    room_id=message.room_id,
                    user_id=message.user_id,
                    username=message.username,
                    display_name=message.display_name,
                    message_type=message.message_type,
                    message=message.content,
                    timestamp=message.timestamp
                ))
            
            logger.info(f"Created {len(saved_messages)} test messages for room {room_id}")
            return saved_messages
            
        except Exception as e:
            logger.error(f"Error creating test messages for room {room_id}: {str(e)}")
            raise

chat_service = ChatService() 
from datetime import datetime
from typing import List, Optional
import logging
from src.modules.chat.models import ChatMessage
from src.modules.chat.enums import ChatType
from src.modules.chat.dto import ChatMessageResponse, RoomChatHistoryResponse
from src.modules.chat.repository import get_chat_repository, ChatRepository

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, chat_repository: ChatRepository = None):
        self.chat_repository = chat_repository or get_chat_repository()
    
    async def save_message(
        self, 
        room_id: str, 
        profile_id: str, 
        display_name: str, 
        message: str, 
        message_type: ChatType = ChatType.LOBBY
    ) -> ChatMessageResponse:
        """Save chat message"""
        try:
            logger.info(f"Saving message in room {room_id} by profile {profile_id}")
            # room_id를 문자열로 저장
            from bson import ObjectId
            try:
                # ObjectId로 변환 시도 후 문자열로 저장
                object_id = ObjectId(room_id)
                room_id_str = str(object_id)
            except:
                # 이미 문자열이면 그대로 사용
                room_id_str = room_id
            
            chat_message = ChatMessage(
                id=None,
                room_id=room_id_str,
                profile_id=profile_id,
                display_name=display_name,
                message_type=message_type,
                message=message,
                timestamp=datetime.utcnow()
            )
            message_id = await self.chat_repository.create(chat_message)
            chat_message.id = message_id
            return ChatMessageResponse(
                id=chat_message.id,
                room_id=chat_message.room_id,
                profile_id=chat_message.profile_id,
                display_name=chat_message.display_name,
                message_type=chat_message.message_type,
                message=chat_message.message,
                timestamp=chat_message.timestamp
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
                    profile_id=m.profile_id, 
                    display_name=m.display_name,
                    message_type=m.message_type,
                    message=m.message,
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
                    "profile_id": "test_profile_1",
                    "display_name": "스타트업 마스터",
                    "message": "안녕하세요! 스타트업 TRPG에 오신 것을 환영합니다!",
                    "message_type": ChatType.LOBBY
                },
                {
                    "profile_id": "test_profile_2", 
                    "display_name": "기술 애호가",
                    "message": "안녕하세요! 기대됩니다!",
                    "message_type": ChatType.LOBBY
                },
                {
                    "profile_id": "test_profile_3",
                    "display_name": "비즈니스 구루",
                    "message": "창업 아이디어를 구상해보죠!",
                    "message_type": ChatType.LOBBY
                }
            ]
            
            saved_messages = []
            for msg_data in test_messages:
                chat_message = ChatMessage(
                    id=None,
                    room_id=room_id_str,
                    profile_id=msg_data["profile_id"],
                    display_name=msg_data["display_name"],
                    message_type=msg_data["message_type"],
                    message=msg_data["message"],
                    timestamp=datetime.utcnow()
                )
                message_id = await self.chat_repository.create(chat_message)
                chat_message.id = message_id
                saved_messages.append(ChatMessageResponse(
                    id=chat_message.id,
                    room_id=chat_message.room_id,
                    profile_id=chat_message.profile_id,
                    display_name=chat_message.display_name,
                    message_type=chat_message.message_type,
                    message=chat_message.message,
                    timestamp=chat_message.timestamp
                ))
            
            logger.info(f"Created {len(saved_messages)} test messages for room {room_id}")
            return saved_messages
            
        except Exception as e:
            logger.error(f"Error creating test messages for room {room_id}: {str(e)}")
            raise

chat_service = ChatService() 
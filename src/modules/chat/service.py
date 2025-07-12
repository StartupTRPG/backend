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
        message_type: ChatType = ChatType.TEXT
    ) -> ChatMessageResponse:
        """채팅 메시지 저장"""
        try:
            logger.info(f"Saving message in room {room_id} by user {username}")
            message = ChatMessage(
                id=None,
                room_id=room_id,
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
        """방의 채팅 메시지 조회 (페이지네이션)"""
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
                    user_id=None,  # user_id 필드는 ChatMessage에 없음. 필요시 모델 수정
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
    
    async def save_system_message(self, room_id: str, content: str) -> ChatMessageResponse:
        logger.info(f"Saving system message in room {room_id}: {content}")
        return await self.save_message(
            room_id=room_id,
            user_id="system",
            username="시스템",
            display_name="시스템",
            content=content,
            message_type=ChatType.SYSTEM
        )
    
    async def delete_room_messages(self, room_id: str) -> int:
        try:
            logger.warning(f"Deleting all messages for room {room_id}")
            # MongoRepository의 delete_many는 직접 구현 필요. 임시로 pass
            # result = await self.chat_repository.delete_many({"room_id": room_id})
            # return result.deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error deleting messages for room {room_id}: {str(e)}")
            raise

chat_service = ChatService() 
from datetime import datetime
from typing import List, Optional
import logging
from bson import ObjectId
from src.core.mongodb import get_collection
from .models import ChatMessage, ChatType
from .dto import ChatMessageResponse, RoomChatHistoryResponse

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """채팅 메시지 컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("chat_messages")
        return self.collection
    
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
            
            message_data = {
                "room_id": room_id,
                "user_id": user_id,
                "username": username,
                "display_name": display_name,
                "message_type": message_type,
                "content": content,
                "timestamp": datetime.utcnow()
            }
            
            result = await self._get_collection().insert_one(message_data)
            
            # 저장된 메시지 조회
            saved_message = await self._get_collection().find_one({"_id": result.inserted_id})
            
            logger.debug(f"Message saved successfully: {result.inserted_id}")
            
            return ChatMessageResponse(
                id=str(saved_message["_id"]),
                room_id=saved_message["room_id"],
                user_id=saved_message["user_id"],
                username=saved_message["username"],
                display_name=saved_message["display_name"],
                message_type=saved_message["message_type"],
                message=saved_message["content"],
                timestamp=saved_message["timestamp"]
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
            
            # 메시지 조회 (최신순)
            cursor = self._get_collection().find(
                {"room_id": room_id}
            ).sort("timestamp", -1).skip(skip).limit(limit)
            
            messages = []
            async for doc in cursor:
                messages.append(ChatMessageResponse(
                    id=str(doc["_id"]),
                    room_id=doc["room_id"],
                    user_id=doc["user_id"],
                    username=doc["username"],
                    display_name=doc["display_name"],
                    message_type=doc["message_type"],
                    message=doc["content"],
                    timestamp=doc["timestamp"]
                ))
            
            # 시간순으로 정렬 (오래된 것부터)
            messages.reverse()
            
            # 총 메시지 수 조회
            total_count = await self._get_collection().count_documents({"room_id": room_id})
            
            logger.debug(f"Found {len(messages)} messages for room {room_id} (total: {total_count})")
            
            return RoomChatHistoryResponse(
                room_id=room_id,
                messages=messages,
                total_count=total_count,
                page=page,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error fetching messages for room {room_id}: {str(e)}")
            raise
    
    async def save_system_message(self, room_id: str, content: str) -> ChatMessageResponse:
        """시스템 메시지 저장"""
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
        """방의 모든 메시지 삭제"""
        try:
            logger.warning(f"Deleting all messages for room {room_id}")
            result = await self._get_collection().delete_many({"room_id": room_id})
            logger.info(f"Deleted {result.deleted_count} messages from room {room_id}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting messages for room {room_id}: {str(e)}")
            raise


# 싱글톤 인스턴스
chat_service = ChatService() 
from datetime import datetime
from typing import List, Optional
import logging
from src.modules.chat.models import ChatMessage
from src.modules.chat.enum import ChatType
from src.modules.chat.dto import ChatMessageResponse, RoomChatHistoryResponse
from src.modules.chat.repository import get_chat_repository, ChatRepository
from src.modules.room.enums import RoomStatus

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, chat_repository: ChatRepository = None):
        self.chat_repository = chat_repository or get_chat_repository()
    
    def _determine_chat_category(self, room_status: RoomStatus, message_type: ChatType) -> str:
        """Determine chat category based on room status and message type"""
        if room_status == RoomStatus.WAITING:
            return "lobby"
        elif room_status == RoomStatus.PLAYING:
            return "game"
        else:
            return "general"
    
    async def save_message(
        self, 
        room_id: str, 
        user_id: str, 
        username: str, 
        display_name: str, 
        content: str, 
        message_type: ChatType = ChatType.LOBBY,
        room_status: RoomStatus = RoomStatus.WAITING
    ) -> ChatMessageResponse:
        """Save chat message"""
        try:
            logger.info(f"Saving message in room {room_id} by user {username}")
            
            # Determine chat category based on room status
            chat_category = self._determine_chat_category(room_status, message_type)
            
            message = ChatMessage(
                id=None,
                room_id=room_id,
                username=username,
                display_name=display_name,
                message_type=message_type,
                content=content,
                timestamp=datetime.utcnow(),
                chat_category=chat_category
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
        limit: int = 50,
        chat_category: Optional[str] = None
    ) -> RoomChatHistoryResponse:
        """Get room chat messages (with pagination)"""
        try:
            logger.info(f"Fetching messages for room {room_id} (page: {page}, limit: {limit}, category: {chat_category})")
            skip = (page - 1) * limit
            
            # Filter by chat category if specified
            filter_query = {"room_id": room_id}
            if chat_category:
                filter_query["chat_category"] = chat_category
                
            messages = await self.chat_repository.find_many(filter_query, skip, limit)
            # Sort by time (oldest first)
            messages = sorted(messages, key=lambda m: m.timestamp)
            
            # Get total message count
            total_count = await self.chat_repository.count(filter_query)
            
            return RoomChatHistoryResponse(
                room_id=room_id,
                messages=[ChatMessageResponse(
                    id=m.id,
                    room_id=m.room_id,
                    user_id=None,  # user_id field not in ChatMessage. Modify model if needed
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
    
    async def get_lobby_messages(self, room_id: str, page: int = 1, limit: int = 50) -> RoomChatHistoryResponse:
        """Get lobby chat messages"""
        return await self.get_room_messages(room_id, page, limit, "lobby")
    
    async def get_game_messages(self, room_id: str, page: int = 1, limit: int = 50) -> RoomChatHistoryResponse:
        """Get game chat messages"""
        return await self.get_room_messages(room_id, page, limit, "game")
    

    
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

chat_service = ChatService() 
from pydantic import BaseModel
from typing import List
from .room_chat_history_response import RoomChatHistoryResponse


class GetChatHistoryResponse(BaseModel):
    """Chat history retrieval response model"""
    data: RoomChatHistoryResponse
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "room_id": "507f1f77bcf86cd799439011",
                    "messages": [
                        {
                            "id": "507f1f77bcf86cd799439012",
                            "room_id": "507f1f77bcf86cd799439011",
                            "user_id": "507f1f77bcf86cd799439013",
                            "username": "testuser",
                            "content": "Hello!",
                            "message_type": "text",
                            "created_at": "2024-01-01T00:00:00"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 50,
                        "total": 1,
                        "has_next": False,
                        "has_prev": False
                    }
                },
                "message": "Chat history retrieved successfully.",
                "success": True
            }
        }


class DeleteChatHistoryResponse(BaseModel):
    """채팅 기록 삭제 응답 모델"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "deleted_count": 10
                },
                "message": "방 507f1f77bcf86cd799439011의 채팅 기록이 삭제되었습니다.",
                "success": True
            }
        } 
from pydantic import BaseModel, Field
from typing import List
from .room_chat_history_response import RoomChatHistoryResponse


class GetChatHistoryResponse(BaseModel):
    """Chat history retrieval response model"""
    data: RoomChatHistoryResponse = Field(..., description="채팅 히스토리 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(..., description="조회 성공 여부")
    
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
                            "username": "startup_master",
                            "content": "안녕하세요! 스타트업 TRPG에 오신 것을 환영합니다!",
                            "message_type": "lobby",
                            "created_at": "2024-01-01T12:00:00"
                        },
                        {
                            "id": "507f1f77bcf86cd799439014",
                            "room_id": "507f1f77bcf86cd799439011",
                            "user_id": "507f1f77bcf86cd799439015",
                            "username": "tech_enthusiast",
                            "content": "안녕하세요! 기대됩니다!",
                            "message_type": "lobby",
                            "created_at": "2024-01-01T12:05:00"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 50,
                        "total": 2,
                        "has_next": False,
                        "has_prev": False
                    }
                },
                "message": "채팅 히스토리를 성공적으로 조회했습니다.",
                "success": True
            }
        }


class DeleteChatHistoryData(BaseModel):
    """채팅 기록 삭제 응답 데이터"""
    deleted_count: int = Field(..., description="삭제된 메시지 수")
    room_id: str = Field(..., description="방 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "deleted_count": 15,
                "room_id": "507f1f77bcf86cd799439011"
            }
        }


class DeleteChatHistoryResponse(BaseModel):
    """채팅 기록 삭제 응답 모델"""
    data: DeleteChatHistoryData = Field(..., description="삭제 결과 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(..., description="삭제 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "deleted_count": 15,
                    "room_id": "507f1f77bcf86cd799439011"
                },
                "message": "방 507f1f77bcf86cd799439011의 채팅 기록이 삭제되었습니다.",
                "success": True
            }
        } 
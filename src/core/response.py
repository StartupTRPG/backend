from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Common API response model"""
    data: T = Field(..., description="응답 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(default=True, description="요청 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439011",
                    "title": "테스트 방",
                    "description": "테스트용 방입니다.",
                    "host_profile_id": "507f1f77bcf86cd799439012",
                    "host_display_name": "testuser",
                    "max_players": 4,
                    "current_players": 2,
                    "status": "waiting",
                    "visibility": "public",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "game_settings": {},
                    "players": [
                        {
                            "profile_id": "507f1f77bcf86cd799439012",
                            "display_name": "testuser",
                            "role": "host",
                            "joined_at": "2024-01-01T00:00:00"
                        }
                    ]
                },
                "message": "방이 성공적으로 생성되었습니다.",
                "success": True
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    message: str = Field(..., description="에러 메시지")
    success: bool = Field(default=False, description="요청 성공 여부")
    error_code: Optional[str] = Field(default=None, description="에러 코드")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "요청 처리 중 오류가 발생했습니다.",
                "success": False,
                "error_code": "INTERNAL_ERROR"
            }
        } 
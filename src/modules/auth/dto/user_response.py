from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class UserData(BaseModel):
    """사용자 정보 데이터"""
    id: str = Field(..., description="사용자 ID")
    username: str = Field(..., description="사용자명")
    email: str = Field(..., description="이메일")
    created_at: datetime = Field(..., description="계정 생성 시간")
    updated_at: Optional[datetime] = Field(None, description="계정 수정 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "username": "startup_master",
                "email": "startup_master@example.com",
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }


class UserResponse(BaseModel):
    """User response model"""
    data: UserData = Field(..., description="사용자 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(..., description="조회 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439012",
                    "username": "startup_master",
                    "email": "startup_master@example.com",
                    "created_at": "2024-01-01T10:00:00",
                    "updated_at": "2024-01-01T12:00:00"
                },
                "message": "사용자 정보를 성공적으로 조회했습니다.",
                "success": True
            }
        } 
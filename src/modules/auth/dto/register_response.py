from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RegisterData(BaseModel):
    """회원가입 응답 데이터"""
    user_id: str
    username: str
    email: str
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "username": "testuser",
                "email": "test@example.com",
                "created_at": "2024-01-01T00:00:00"
            }
        }


class RegisterResponse(BaseModel):
    """회원가입 응답 모델"""
    data: RegisterData
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "user_id": "507f1f77bcf86cd799439011",
                    "username": "testuser",
                    "email": "test@example.com",
                    "created_at": "2024-01-01T00:00:00"
                },
                "message": "회원가입이 완료되었습니다. 로그인해주세요.",
                "success": True
            }
        } 
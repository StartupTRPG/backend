from pydantic import BaseModel
from typing import Optional


class RefreshResponse(BaseModel):
    """토큰 갱신 응답 모델"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "message": "토큰이 성공적으로 갱신되었습니다.",
                "success": True
            }
        } 
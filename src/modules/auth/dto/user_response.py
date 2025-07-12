from pydantic import BaseModel


class UserResponse(BaseModel):
    """사용자 정보 조회 응답 모델"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439011",
                    "username": "testuser",
                    "email": "test@example.com",
                    "nickname": "테스트유저",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-01T00:00:00"
                },
                "message": "사용자 정보를 성공적으로 조회했습니다.",
                "success": True
            }
        } 
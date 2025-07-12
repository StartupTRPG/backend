from pydantic import BaseModel


class UserResponse(BaseModel):
    """User information retrieval response model"""
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
                    "nickname": "TestUser",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "last_login": "2024-01-01T00:00:00"
                },
                "message": "User information retrieved successfully.",
                "success": True
            }
        } 
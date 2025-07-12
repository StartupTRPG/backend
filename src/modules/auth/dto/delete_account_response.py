from pydantic import BaseModel


class DeleteAccountData(BaseModel):
    """계정 삭제 응답 데이터"""
    user_id: str
    username: str
    deleted_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "username": "testuser",
                "deleted_at": "2024-01-01T00:00:00"
            }
        }


class DeleteAccountResponse(BaseModel):
    """Delete account response model"""
    data: DeleteAccountData
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "user_id": "507f1f77bcf86cd799439011",
                    "username": "testuser",
                    "deleted_at": "2024-01-01T00:00:00"
                },
                "message": "Account deleted successfully.",
                "success": True
            }
        } 
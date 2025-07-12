from pydantic import BaseModel


class RefreshData(BaseModel):
    """토큰 갱신 응답 데이터"""
    access_token: str
    token_type: str
    expires_in: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class RefreshResponse(BaseModel):
    """Refresh token response model"""
    data: RefreshData
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
                "message": "Token refreshed successfully.",
                "success": True
            }
        } 
from pydantic import BaseModel


class LoginResponse(BaseModel):
    """Login response model"""
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
                "message": "Login successful.",
                "success": True
            }
        } 
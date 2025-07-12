from pydantic import BaseModel


class LoginResponse(BaseModel):
    """로그인 응답 모델"""
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
                "message": "로그인이 성공했습니다.",
                "success": True
            }
        } 
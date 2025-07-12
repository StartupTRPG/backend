from pydantic import BaseModel, Field


class LoginData(BaseModel):
    """로그인 응답 데이터"""
    access_token: str = Field(..., description="액세스 토큰")
    token_type: str = Field(..., description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간(초)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTIiLCJ1c2VybmFtZSI6InN0YXJ0dXBfbWFzdGVyIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTcwNDE2ODAwMH0.example_signature",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class LoginResponse(BaseModel):
    """Login response model"""
    data: LoginData = Field(..., description="로그인 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(..., description="로그인 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MDdmMWY3N2JjZjg2Y2Q3OTk0MzkwMTIiLCJ1c2VybmFtZSI6InN0YXJ0dXBfbWFzdGVyIiwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTcwNDE2ODAwMH0.example_signature",
                    "token_type": "bearer",
                    "expires_in": 3600
                },
                "message": "로그인이 성공했습니다.",
                "success": True
            }
        } 
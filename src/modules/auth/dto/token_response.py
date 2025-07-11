from pydantic import BaseModel
from src.modules.user.dto import UserResponse

class TokenResponse(BaseModel):
    """토큰 응답 DTO"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse 
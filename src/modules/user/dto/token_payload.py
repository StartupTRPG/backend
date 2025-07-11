from pydantic import BaseModel

class TokenPayload(BaseModel):
    """JWT 토큰 페이로드 DTO"""
    user_id: str
    username: str
    type: str  # "access" or "refresh"
    exp: int
    iat: int 
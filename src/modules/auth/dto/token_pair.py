from pydantic import BaseModel

class TokenPair(BaseModel):
    """액세스/리프레시 토큰 쌍 DTO (사용자 정보 없음)"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int 
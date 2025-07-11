from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 DTO"""
    refresh_token: str 
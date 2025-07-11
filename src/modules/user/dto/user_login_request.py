from pydantic import BaseModel

class UserLoginRequest(BaseModel):
    """사용자 로그인 요청 DTO"""
    username: str
    password: str 
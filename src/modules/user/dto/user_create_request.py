from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreateRequest(BaseModel):
    """사용자 생성 요청 DTO"""
    username: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    password: str 
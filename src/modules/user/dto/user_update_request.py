from pydantic import BaseModel, EmailStr
from typing import Optional

class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청 DTO"""
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None 
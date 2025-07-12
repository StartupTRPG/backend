from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserDocument(BaseModel):
    """MongoDB 문서 형태의 사용자 모델"""
    id: Optional[str] = None  # MongoDB _id를 문자열로 변환한 값
    username: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    password: str  # 해시된 비밀번호
    salt: Optional[str] = None  # PBKDF2 salt
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
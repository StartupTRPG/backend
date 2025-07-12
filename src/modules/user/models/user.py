from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """사용자 데이터베이스 스키마"""
    id: Optional[str] = None
    username: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    password: str  # 해시된 비밀번호
    salt: Optional[str] = None  # PBKDF2 salt
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
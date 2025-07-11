from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """사용자 데이터베이스 스키마"""
    id: str
    username: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
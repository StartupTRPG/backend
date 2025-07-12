from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserDocument(BaseModel):
    """User model in MongoDB document format"""
    id: Optional[str] = None  # MongoDB _id converted to string
    username: str
    email: Optional[EmailStr] = None
    nickname: Optional[str] = None
    password: str  # Hashed password
    salt: Optional[str] = None  # PBKDF2 salt
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
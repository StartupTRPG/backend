from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfileResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    user_level: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfilePublicResponse(BaseModel):
    """공개 프로필 응답 (다른 사용자가 볼 수 있는 정보)"""
    user_id: str
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    user_level: int
    created_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserProfileDocument(BaseModel):
    id: Optional[str] = None
    user_id: str
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    user_level: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 
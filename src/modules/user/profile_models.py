from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserProfileCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=30, description="표시 이름")
    bio: Optional[str] = Field(None, max_length=500, description="자기소개")
    avatar_url: Optional[str] = Field(None, description="아바타 이미지 URL")
    user_level: int = Field(1, ge=1, le=100, description="사용자 레벨 (1-100)")

class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=30, description="표시 이름")
    bio: Optional[str] = Field(None, max_length=500, description="자기소개")
    avatar_url: Optional[str] = Field(None, description="아바타 이미지 URL")
    user_level: Optional[int] = Field(None, ge=1, le=100, description="사용자 레벨 (1-100)")

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    username: str
    display_name: str
    bio: Optional[str]
    avatar_url: Optional[str]
    user_level: int
    created_at: datetime
    updated_at: datetime
    
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
    
    class Config:
        from_attributes = True 
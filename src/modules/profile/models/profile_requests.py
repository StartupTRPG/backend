from pydantic import BaseModel, Field
from typing import Optional


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=30, description="표시 이름")
    bio: Optional[str] = Field(None, max_length=500, description="자기소개")
    avatar_url: Optional[str] = Field(None, description="아바타 이미지 URL")
    user_level: Optional[int] = Field(None, ge=1, le=100, description="사용자 레벨 (1-100)") 
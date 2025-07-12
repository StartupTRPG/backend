from pydantic import BaseModel
from typing import List
from ..models import UserProfileResponse, UserProfilePublicResponse


class CreateProfileResponse(BaseModel):
    """프로필 생성 응답 모델"""
    data: UserProfileResponse
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439011",
                    "user_id": "507f1f77bcf86cd799439012",
                    "display_name": "테스트유저",
                    "bio": "안녕하세요! 테스트유저입니다.",
                    "user_level": 1,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                },
                "message": "프로필이 성공적으로 생성되었습니다.",
                "success": True
            }
        }


class GetProfileResponse(BaseModel):
    """프로필 조회 응답 모델"""
    data: UserProfileResponse
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439011",
                    "user_id": "507f1f77bcf86cd799439012",
                    "display_name": "테스트유저",
                    "bio": "안녕하세요! 테스트유저입니다.",
                    "user_level": 1,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                },
                "message": "프로필을 성공적으로 조회했습니다.",
                "success": True
            }
        }


class UpdateProfileResponse(BaseModel):
    """프로필 수정 응답 모델"""
    data: UserProfileResponse
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "507f1f77bcf86cd799439011",
                    "user_id": "507f1f77bcf86cd799439012",
                    "display_name": "수정된유저",
                    "bio": "수정된 자기소개입니다.",
                    "user_level": 2,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                },
                "message": "프로필이 성공적으로 수정되었습니다.",
                "success": True
            }
        }


class GetUserProfileResponse(BaseModel):
    """다른 사용자 프로필 조회 응답 모델"""
    data: UserProfilePublicResponse
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "user_id": "507f1f77bcf86cd799439012",
                    "display_name": "테스트유저",
                    "bio": "안녕하세요! 테스트유저입니다.",
                    "user_level": 1
                },
                "message": "사용자 프로필을 성공적으로 조회했습니다.",
                "success": True
            }
        }


class SearchProfilesResponse(BaseModel):
    """프로필 검색 응답 모델"""
    data: List[UserProfilePublicResponse]
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "user_id": "507f1f77bcf86cd799439012",
                        "display_name": "테스트유저1",
                        "bio": "안녕하세요! 테스트유저1입니다.",
                        "user_level": 1
                    },
                    {
                        "user_id": "507f1f77bcf86cd799439013",
                        "display_name": "테스트유저2",
                        "bio": "안녕하세요! 테스트유저2입니다.",
                        "user_level": 2
                    }
                ],
                "message": "'테스트' 검색 결과를 성공적으로 조회했습니다.",
                "success": True
            }
        } 
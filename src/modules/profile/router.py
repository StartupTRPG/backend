from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from src.modules.user.dto import UserResponse
from src.modules.user.service import user_service
from src.core.jwt_utils import jwt_manager
from .service import user_profile_service
from .models import UserProfileCreate, UserProfileUpdate, UserProfileResponse, UserProfilePublicResponse
from .dto import (
    CreateProfileResponse, GetProfileResponse, UpdateProfileResponse,
    GetUserProfileResponse, SearchProfilesResponse
)

router = APIRouter(prefix="/profile", tags=["User Profile"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """Dependency to get current user info"""
    try:
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid access token.")
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type.")
        user = await user_service.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found.")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error occurred while retrieving user info.")

@router.post("", response_model=CreateProfileResponse)
async def create_profile(
    profile_data: UserProfileCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """사용자 프로필 생성"""
    try:
        profile = await user_profile_service.create_profile(current_user, profile_data)
        return CreateProfileResponse(
            data=profile,
            message="Profile created successfully.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=GetProfileResponse)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """내 프로필 조회"""
    try:
        profile = await user_profile_service.get_profile(current_user.id)
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail="Profile not found. Please create a profile first using POST /profile."
            )
        return GetProfileResponse(
            data=profile,
            message="Profile retrieved successfully.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while retrieving profile: {str(e)}")

@router.put("/me", response_model=UpdateProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """내 프로필 수정"""
    try:
        profile = await user_profile_service.update_profile(current_user.id, profile_data)
        if not profile:
            raise HTTPException(
                status_code=404, 
                detail="Profile not found. Please create a profile first using POST /profile."
            )
        return UpdateProfileResponse(
            data=profile,
            message="Profile updated successfully.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=GetUserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """다른 사용자의 공개 프로필 조회 (인증된 유저만)"""
    try:
        profile = await user_profile_service.get_public_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Public profile not found.")
        return GetUserProfileResponse(
            data=profile,
            message="User profile retrieved successfully.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while retrieving profile: {str(e)}")

@router.get("/search", response_model=SearchProfilesResponse)
async def search_profiles(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Limit results"),
    current_user: UserResponse = Depends(get_current_user)
):
    """프로필 검색 (사용자 찾기) - 인증된 유저만"""
    try:
        profiles = await user_profile_service.search_profiles(q, limit)
        return SearchProfilesResponse(
            data=profiles,
            message=f"'{q}' search results retrieved successfully.",
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred while searching profiles: {str(e)}")

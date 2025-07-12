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

router = APIRouter(prefix="/profile", tags=["사용자 프로필"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """현재 사용자 정보를 가져오는 의존성"""
    try:
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 액세스 토큰입니다.")
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
        
        user = await user_service.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다.")

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
            message="프로필이 성공적으로 생성되었습니다.",
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
                detail="프로필이 없습니다. POST /profile로 프로필을 먼저 생성해주세요."
            )
        return GetProfileResponse(
            data=profile,
            message="프로필을 성공적으로 조회했습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}")

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
                detail="프로필이 없습니다. POST /profile로 프로필을 먼저 생성해주세요."
            )
        return UpdateProfileResponse(
            data=profile,
            message="프로필이 성공적으로 수정되었습니다.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=GetUserProfileResponse)
async def get_user_profile(user_id: str):
    """다른 사용자의 공개 프로필 조회"""
    try:
        profile = await user_profile_service.get_public_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="공개 프로필을 찾을 수 없습니다.")
        return GetUserProfileResponse(
            data=profile,
            message="사용자 프로필을 성공적으로 조회했습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/search", response_model=SearchProfilesResponse)
async def search_profiles(
    q: str = Query(..., min_length=2, description="검색어"),
    limit: int = Query(20, ge=1, le=50, description="결과 수 제한")
):
    """프로필 검색 (사용자 찾기)"""
    try:
        profiles = await user_profile_service.search_profiles(q, limit)
        return SearchProfilesResponse(
            data=profiles,
            message=f"'{q}' 검색 결과를 성공적으로 조회했습니다.",
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 검색 중 오류가 발생했습니다: {str(e)}")

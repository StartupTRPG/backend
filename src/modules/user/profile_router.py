from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from src.modules.user.models import UserResponse
from src.modules.user.service import user_service
from src.core.jwt_utils import jwt_manager
from .profile_service import user_profile_service
from .profile_models import UserProfilePublicResponse, UserProfileResponse, UserProfileUpdate, UserProfileCreate

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

@router.post("", response_model=UserProfileResponse)
async def create_profile(
    profile_data: UserProfileCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """사용자 프로필 생성"""
    try:
        profile = await user_profile_service.create_profile(current_user, profile_data)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me", response_model=UserProfileResponse)
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
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}")

@router.put("/me", response_model=UserProfileResponse)
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
        return profile
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=UserProfilePublicResponse)
async def get_user_profile(user_id: str):
    """다른 사용자의 공개 프로필 조회"""
    try:
        profile = await user_profile_service.get_public_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="공개 프로필을 찾을 수 없습니다.")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/search", response_model=List[UserProfilePublicResponse])
async def search_profiles(
    q: str = Query(..., min_length=2, description="검색어"),
    limit: int = Query(20, ge=1, le=50, description="결과 수 제한")
):
    """프로필 검색 (사용자 찾기)"""
    try:
        profiles = await user_profile_service.search_profiles(q, limit)
        return profiles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 검색 중 오류가 발생했습니다: {str(e)}")

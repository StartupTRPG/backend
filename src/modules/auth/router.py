import logging
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.modules.user.service import user_service
from src.modules.user.dto import UserCreateRequest, UserLoginRequest
from src.modules.auth.dto import TokenResponse, RefreshTokenRequest
from src.modules.profile.service import user_profile_service
from src.modules.profile.models import UserProfileCreate
from src.core.jwt_utils import jwt_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])
security = HTTPBearer()

@router.post("/register")
async def register(user_data: UserCreateRequest):
    """사용자 회원가입 - 계정 생성만 처리"""
    try:
        user = await user_service.create_user(user_data)
        
        # 기본 프로필 자동 생성
        try:
            default_profile = UserProfileCreate(
                display_name=user.username,
                bio=f"안녕하세요! {user.username}입니다.",
                user_level=1
            )
            await user_profile_service.create_profile(user, default_profile)
        except Exception as e:
            # 프로필 생성 실패는 로그만 남기고 회원가입은 계속 진행
            print(f"프로필 생성 실패: {e}")
        
        return {
            "message": "회원가입이 완료되었습니다. 로그인해주세요.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("회원가입 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다.")

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLoginRequest):
    """사용자 로그인 - 토큰 발급 (응답으로만 전달)"""
    try:
        user = await user_service.authenticate_user(login_data)
        if not user:
            raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호입니다.")
        
        tokens = user_service.create_tokens(user)
        
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("로그인 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다.")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """토큰 갱신"""
    try:
        if not refresh_data.refresh_token or refresh_data.refresh_token.strip() == "":
            raise HTTPException(status_code=400, detail="리프레시 토큰이 필요합니다.")
        
        payload = jwt_manager.verify_token(refresh_data.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
        
        user = await user_service.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        
        tokens = user_service.create_tokens(user)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("토큰 갱신 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다.")

@router.get("/me", dependencies=[Depends(security)])
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회"""
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
        logger.exception("사용자 정보 조회 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다.")

@router.post("/logout")
async def logout():
    """사용자 로그아웃 - 클라이언트에서 토큰 삭제 필요"""
    try:
        return {
            "message": "로그아웃이 완료되었습니다. 클라이언트에서 토큰을 삭제해주세요.",
            "instructions": {
                "client_action": "토큰을 로컬 저장소에서 삭제하고 Socket.IO 연결을 해제하세요."
            }
        }
    except Exception as e:
        logger.exception("로그아웃 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="로그아웃 중 오류가 발생했습니다.")

@router.delete("/account", dependencies=[Depends(security)])
async def delete_account(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """계정 삭제 (프로필도 함께 삭제)"""
    try:
        # 현재 사용자 확인
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 액세스 토큰입니다.")
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
        
        user_id = payload["user_id"]
        
        # 계정 삭제 (프로필도 함께 삭제됨)
        success = await user_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=400, detail="계정 삭제에 실패했습니다.")
        
        return {
            "message": "계정이 성공적으로 삭제되었습니다.",
            "instructions": {
                "client_action": "모든 토큰을 삭제하고 로그인 페이지로 이동하세요."
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("계정 삭제 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="계정 삭제 중 오류가 발생했습니다.")

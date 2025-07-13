import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.modules.user.service import user_service
from src.modules.user.dto import UserCreateRequest, UserLoginRequest
from src.modules.auth.dto import (
    TokenData, RefreshTokenRequest, RegisterData, RegisterResponse, 
    RefreshResponse, LoginResponse, UserResponse, LogoutResponse, DeleteAccountResponse
)
from src.modules.profile.service import user_profile_service
from src.modules.profile.models import UserProfileCreate
from src.core.jwt_utils import jwt_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["인증"])
security = HTTPBearer()

@router.post("/register", response_model=RegisterResponse)
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
            await user_profile_service.create_new_profile(user)
        except Exception as e:
            # 프로필 생성 실패는 로그만 남기고 회원가입은 계속 진행
            print(f"프로필 생성 실패: {e}")
        
        data = RegisterData(
            user_id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
        
        return RegisterResponse(
            data=data,
            message="회원가입이 완료되었습니다. 로그인해주세요.",
            success=True
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("회원가입 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다.")

@router.post("/login", response_model=LoginResponse)
async def login(login_data: UserLoginRequest, response: Response):
    """사용자 로그인 - 토큰 발급 (refresh token은 HTTP-only 쿠키로 설정)"""
    try:
        user = await user_service.authenticate_user(login_data)
        if not user:
            raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호입니다.")
        
        tokens = user_service.create_tokens(user)
        
        # refresh token을 HTTP-only 쿠키로 설정
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=False,  # 개발환경에서는 False, 프로덕션에서는 True
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7일
        )
        
        from .dto.login_response import LoginData
        login_data = LoginData(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in
        )
        
        return LoginResponse(
            data=login_data,
            message="로그인이 성공했습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("로그인 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다.")

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: Request, response: Response):
    """토큰 갱신 - 쿠키에서 refresh token 읽기"""
    try:
        # 쿠키에서 refresh token 읽기
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="리프레시 토큰이 필요합니다.")
        
        payload = jwt_manager.verify_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
        
        user = await user_service.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        
        tokens = user_service.create_tokens(user)
        
        # 새로운 refresh token을 HTTP-only 쿠키로 설정
        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=False,  # 개발환경에서는 False, 프로덕션에서는 True
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7일
        )
        
        from .dto.refresh_response import RefreshData
        refresh_data = RefreshData(
            access_token=tokens.access_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in
        )
        
        return RefreshResponse(
            data=refresh_data,
            message="토큰이 성공적으로 갱신되었습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("토큰 갱신 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="토큰 갱신 중 오류가 발생했습니다.")

@router.get("/me", response_model=UserResponse, dependencies=[Depends(security)])
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
        
        from .dto.user_response import UserData
        user_data = UserData(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        return UserResponse(
            data=user_data,
            message="사용자 정보를 성공적으로 조회했습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("사용자 정보 조회 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다.")

@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response):
    """사용자 로그아웃 - refresh token 쿠키 삭제"""
    try:
        # refresh token 쿠키 삭제
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=False,
            samesite="lax"
        )
        
        from .dto.logout_response import LogoutData
        logout_data = LogoutData(
            instructions={
                "client_action": "액세스 토큰을 로컬 저장소에서 삭제하고 Socket.IO 연결을 해제하세요."
            }
        )
        return LogoutResponse(
            data=logout_data,
            message="로그아웃이 완료되었습니다. 클라이언트에서 액세스 토큰을 삭제해주세요.",
            success=True
        )
    except Exception as e:
        logger.exception("로그아웃 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="로그아웃 중 오류가 발생했습니다.")

@router.delete("/account", response_model=DeleteAccountResponse, dependencies=[Depends(security)])
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
        
        from datetime import datetime
        from .dto.delete_account_response import DeleteAccountData
        delete_data = DeleteAccountData(
            user_id=user_id,
            username=user.username if user else "unknown",
            deleted_at=datetime.utcnow().isoformat()
        )
        return DeleteAccountResponse(
            data=delete_data,
            message="계정이 성공적으로 삭제되었습니다.",
            success=True
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("계정 삭제 중 오류가 발생했습니다.")
        raise HTTPException(status_code=500, detail="계정 삭제 중 오류가 발생했습니다.")

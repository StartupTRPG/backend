from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.modules.user.service import user_service
from src.modules.user.models import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest
from src.core.jwt_utils import jwt_manager

router = APIRouter(prefix="/auth", tags=["인증"])
security = HTTPBearer()

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """사용자 회원가입"""
    try:
        user = await user_service.create_user(user_data)
        tokens = user_service.create_tokens(user)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다.")

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """사용자 로그인"""
    user = await user_service.authenticate_user(login_data)
    if not user:
        raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호입니다.")
    
    tokens = user_service.create_tokens(user)
    return tokens

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """토큰 갱신"""
    payload = jwt_manager.verify_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="유효하지 않은 리프레시 토큰입니다.")
    
    user = await user_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    
    tokens = user_service.create_tokens(user)
    return tokens

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회"""
    payload = jwt_manager.verify_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="유효하지 않은 액세스 토큰입니다.")
    
    user = await user_service.get_user_by_id(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    
    return user

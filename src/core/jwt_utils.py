from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

class JWTManager:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """액세스 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """리프레시 토큰 생성"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except Exception as e:
            logger.error(f"토큰 검증 중 오류가 발생했습니다: {e}")
            return None
    
    def update_token_with_room_info(self, token: str, room_id: str, room_permissions: str = "write") -> str:
        """기존 토큰에 방 정보 추가"""
        try:
            # 기존 토큰 디코드
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 방 정보 추가
            payload.update({
                "room_id": room_id,
                "room_permissions": room_permissions,
                "room_joined_at": datetime.utcnow().isoformat()
            })
            
            # 새 토큰 생성 (기존 만료 시간 유지)
            new_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Updated token with room info: room_id={room_id}, user_id={payload.get('user_id')}")
            return new_token
            
        except Exception as e:
            logger.error(f"Failed to update token with room info: {str(e)}")
            raise Exception("토큰 업데이트에 실패했습니다.")
    
    def remove_room_info_from_token(self, token: str) -> str:
        """토큰에서 방 정보 제거"""
        try:
            # 기존 토큰 디코드
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 방 정보 제거
            payload.pop("room_id", None)
            payload.pop("room_permissions", None)
            payload.pop("room_joined_at", None)
            
            # 새 토큰 생성
            new_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.info(f"Removed room info from token for user_id={payload.get('user_id')}")
            return new_token
            
        except Exception as e:
            logger.error(f"Failed to remove room info from token: {str(e)}")
            raise Exception("토큰에서 방 정보 제거에 실패했습니다.")
    
    def get_room_info_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰에서 방 정보 추출"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            room_info = {
                "room_id": payload.get("room_id"),
                "room_permissions": payload.get("room_permissions"),
                "room_joined_at": payload.get("room_joined_at")
            }
            
            # 방 정보가 모두 있는지 확인
            if all(room_info.values()):
                return room_info
            return None
            
        except Exception as e:
            logger.error(f"Failed to get room info from token: {str(e)}")
            return None
    
    def create_token_pair(self, user_id: str, username: str):
        """액세스 토큰과 리프레시 토큰 쌍 생성"""
        from src.modules.auth.dto import TokenPair
        user_data = {
            "user_id": user_id,
            "username": username
        }
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )

# 전역 JWT 매니저 인스턴스
jwt_manager = JWTManager()

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """현재 사용자 정보 조회"""
    from src.modules.user.service import user_service
    
    try:
        # 토큰 검증
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 사용자 정보 조회
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰에 사용자 정보가 없습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자를 찾을 수 없습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 검증 중 오류가 발생했습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) 
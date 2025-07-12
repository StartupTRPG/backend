import hashlib
import secrets
from datetime import datetime
from typing import Optional, Tuple
from bson import ObjectId
from src.core.jwt_utils import jwt_manager
from .dto import UserCreateRequest, UserLoginRequest, UserResponse
from src.modules.auth.dto import TokenData
from .repository import get_user_repository, UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or get_user_repository()
    
    def generate_salt(self) -> str:
        """사용자별 고유 salt 생성"""
        return secrets.token_hex(32)  # 64자리 hex 문자열
    
    def hash_password_with_salt(self, password: str, salt: str) -> str:
        """비밀번호와 salt를 사용한 해싱"""
        # PBKDF2 사용 (더 안전한 단방향 해싱)
        hashed = hashlib.pbkdf2_hmac(
            'sha256',  # 해시 알고리즘
            password.encode('utf-8'),  # 비밀번호
            salt.encode('utf-8'),  # salt
            100000  # 반복 횟수 (더 높을수록 안전)
        )
        return hashed.hex()
    
    def create_password_hash(self, password: str) -> Tuple[str, str]:
        """비밀번호 해싱 (salt 생성 포함)"""
        salt = self.generate_salt()
        hashed_password = self.hash_password_with_salt(password, salt)
        return hashed_password, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """비밀번호 검증"""
        return self.hash_password_with_salt(password, salt) == hashed_password
    
    async def create_user(self, user_data: UserCreateRequest) -> UserResponse:
        """사용자 생성"""
        # 중복 사용자명 확인
        existing_user = await self.user_repository.find_by_username(user_data.username)
        if existing_user:
            raise ValueError("이미 존재하는 사용자명입니다.")
        
        # 비밀번호 해싱 (salt 포함)
        hashed_password, salt = self.create_password_hash(user_data.password)
        
        # 사용자 엔티티 생성
        from .models import User
        user = User(
            username=user_data.username,
            email=user_data.email,
            nickname=user_data.nickname or user_data.username,
            password=hashed_password,
            salt=salt,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login=None
        )
        
        # Repository를 통해 저장
        user_id = await self.user_repository.create(user)
        user.id = user_id
        
        # UserResponse로 변환 (비밀번호 정보 제거)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    
    async def authenticate_user(self, login_data: UserLoginRequest) -> Optional[UserResponse]:
        """사용자 인증"""
        user = await self.user_repository.find_by_username(login_data.username)
        if not user:
            return None
        
        # salt가 없는 사용자는 인증 실패 (새로운 방식만 지원)
        if not user.salt:
            return None
        
        # PBKDF2 + salt 방식으로 비밀번호 검증
        if not self.verify_password(login_data.password, user.password, user.salt):
            return None
        
        # 마지막 로그인 시간 업데이트
        await self.user_repository.update_last_login(user.id)
        
        # UserResponse로 변환 (비밀번호 정보 제거)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """사용자 ID로 조회"""
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            return None
        
        # UserResponse로 변환 (비밀번호 정보 제거)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
    
    def create_tokens(self, user: UserResponse) -> TokenData:
        """토큰 쌍 생성"""
        from src.core.jwt_utils import jwt_manager
        token_pair = jwt_manager.create_token_pair(user.id, user.username)
        return TokenData(**token_pair.model_dump(), user=user)
    
    async def delete_user(self, user_id: str) -> bool:
        """사용자 계정 삭제 (프로필도 함께 삭제)"""
        try:
            # 사용자 삭제
            success = await self.user_repository.delete(user_id)
            
            if success:
                # 프로필도 함께 삭제
                try:
                    from src.modules.profile.service import user_profile_service
                    await user_profile_service.delete_profile(user_id)
                except Exception as e:
                    # 프로필 삭제 실패는 로그만 남김
                    print(f"프로필 삭제 실패: {e}")
                
                return True
            
            return False
            
        except Exception:
            return False
    
    async def update_user_role(self, user_id: str, role: str, is_admin: bool = False) -> bool:
        """사용자 역할 업데이트 (관리자용)"""
        try:
            success = await self.user_repository.update(user_id, {
                'role': role,
                'is_admin': is_admin,
                'updated_at': datetime.utcnow()
            })
            return success
        except Exception:
            return False
    
    async def get_user_by_id_with_admin_info(self, user_id: str) -> Optional[UserResponse]:
        """사용자 ID로 조회 (관리자 정보 포함)"""
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            return None
        
        # UserResponse로 변환 (관리자 정보 포함)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            is_admin=getattr(user, 'is_admin', False),
            role=getattr(user, 'role', 'user')
        )

# 전역 서비스 인스턴스 (의존성 주입을 위해 Repository를 주입)
user_service = UserService() 
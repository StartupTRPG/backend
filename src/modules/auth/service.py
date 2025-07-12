import hashlib
import logging
from datetime import datetime
from typing import Optional
from bson import ObjectId
from src.modules.user.dto import UserResponse
from src.modules.auth.dto import TokenResponse
from src.core.jwt_utils import jwt_manager
from src.modules.user.repository import get_user_repository, UserRepository

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or get_user_repository()
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return self._hash_password(password) == hashed_password
    
    async def register_user(self, username: str, password: str) -> Optional[UserResponse]:
        """사용자 회원가입 (토큰 발급 안함)"""
        try:
            logger.info(f"Attempting to register user: {username}")
            
            # 사용자명 중복 확인
            existing_user = await self.user_repository.find_by_username(username)
            if existing_user:
                logger.warning(f"Registration failed: username '{username}' already exists")
                raise ValueError("이미 사용 중인 사용자명입니다.")
            
            # 비밀번호 해싱
            hashed_password = self._hash_password(password)
            
            # 사용자 엔티티 생성
            from src.modules.user.models import User
            user = User(
                username=username,
                password=hashed_password,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Repository를 통해 저장
            user_id = await self.user_repository.create(user)
            user.id = user_id
            
            logger.info(f"User registered successfully: {username} (ID: {user_id})")
            
            return UserResponse(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Registration error for user '{username}': {str(e)}")
            raise ValueError("회원가입 중 오류가 발생했습니다.")

    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """사용자 인증"""
        try:
            logger.info(f"Attempting to authenticate user: {username}")
            
            # 사용자 조회
            user = await self.user_repository.find_by_username(username)
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None
            
            # 비밀번호 검증
            if not self._verify_password(password, user.password):
                logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None
            
            logger.info(f"User authenticated successfully: {username}")
            
            return UserResponse(
                id=user.id,
                username=user.username,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
        except Exception as e:
            logger.error(f"Authentication error for user '{username}': {str(e)}")
            return None

    async def login_user(self, username: str, password: str) -> Optional[TokenResponse]:
        """사용자 로그인 (토큰 발급)"""
        try:
            logger.info(f"Login attempt for user: {username}")
            
            # 사용자 인증
            user = await self.authenticate_user(username, password)
            if not user:
                logger.warning(f"Login failed: authentication failed for user '{username}'")
                return None
            
            # 토큰 생성
            tokens = jwt_manager.create_token_pair(user.id, user.username)
            
            logger.info(f"Login successful for user: {username}")
            
            return tokens
            
        except Exception as e:
            logger.error(f"Login error for user '{username}': {str(e)}")
            return None

# 싱글톤 인스턴스 (의존성 주입을 위해 Repository를 주입)
auth_service = AuthService() 
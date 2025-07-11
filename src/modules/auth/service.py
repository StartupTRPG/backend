import hashlib
import logging
from datetime import datetime
from typing import Optional
from bson import ObjectId
from src.core.mongodb import get_collection
from src.modules.user.dto import UserResponse, TokenResponse
from src.core.jwt_utils import jwt_manager

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """사용자 컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("users")
        return self.collection
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return self._hash_password(password) == hashed_password
    
    async def register_user(self, username: str, password: str) -> Optional[UserResponse]:
        """사용자 회원가입 (토큰 발급 안함)"""
        collection = self._get_collection()
        
        try:
            logger.info(f"Attempting to register user: {username}")
            
            # 사용자명 중복 확인
            existing_user = await collection.find_one({"username": username})
            if existing_user:
                logger.warning(f"Registration failed: username '{username}' already exists")
                raise ValueError("이미 사용 중인 사용자명입니다.")
            
            # 비밀번호 해싱
            hashed_password = self._hash_password(password)
            
            # 사용자 문서 생성
            user_doc = {
                "username": username,
                "password_hash": hashed_password,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(user_doc)
            user_id = str(result.inserted_id)
            
            logger.info(f"User registered successfully: {username} (ID: {user_id})")
            
            return UserResponse(
                id=user_id,
                username=username,
                created_at=user_doc["created_at"],
                updated_at=user_doc["updated_at"]
            )
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Registration error for user '{username}': {str(e)}")
            raise ValueError("회원가입 중 오류가 발생했습니다.")

    async def authenticate_user(self, username: str, password: str) -> Optional[UserResponse]:
        """사용자 인증"""
        collection = self._get_collection()
        
        try:
            logger.info(f"Attempting to authenticate user: {username}")
            
            # 사용자 조회
            user_doc = await collection.find_one({"username": username})
            if not user_doc:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None
            
            # 비밀번호 검증
            if not self._verify_password(password, user_doc["password_hash"]):
                logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None
            
            logger.info(f"User authenticated successfully: {username}")
            
            return UserResponse(
                id=str(user_doc["_id"]),
                username=user_doc["username"],
                created_at=user_doc["created_at"],
                updated_at=user_doc["updated_at"]
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

# 싱글톤 인스턴스
auth_service = AuthService() 
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Tuple
from bson import ObjectId
from src.core.mongodb import get_collection
from src.core.jwt_utils import jwt_manager
from .models import UserCreate, UserLogin, UserResponse, TokenResponse

class UserService:
    def __init__(self):
        self.collection = None
    
    def _get_collection(self):
        """컬렉션을 지연 로딩"""
        if self.collection is None:
            self.collection = get_collection("users")
        return self.collection
    
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
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """사용자 생성"""
        collection = self._get_collection()
        # 중복 사용자명 확인
        existing_user = await collection.find_one({"username": user_data.username})
        if existing_user:
            raise ValueError("이미 존재하는 사용자명입니다.")
        
        # 비밀번호 해싱 (salt 포함)
        hashed_password, salt = self.create_password_hash(user_data.password)
        
        # 사용자 문서 생성
        user_doc = {
            "username": user_data.username,
            "email": user_data.email,
            "nickname": user_data.nickname or user_data.username,
            "password": hashed_password,
            "salt": salt,  # salt를 DB에 저장
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = await collection.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)  # _id를 id로 변경
        del user_doc["password"]  # 비밀번호 제거
        del user_doc["salt"]  # salt 제거
        
        return UserResponse(**user_doc)
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[UserResponse]:
        """사용자 인증"""
        collection = self._get_collection()
        user_doc = await collection.find_one({"username": login_data.username})
        if not user_doc:
            return None
        
        # salt가 없는 사용자는 인증 실패 (새로운 방식만 지원)
        if "salt" not in user_doc:
            return None
        
        # PBKDF2 + salt 방식으로 비밀번호 검증
        if not self.verify_password(login_data.password, user_doc["password"], user_doc["salt"]):
            return None
        
        # 마지막 로그인 시간 업데이트
        await collection.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        user_doc["id"] = str(user_doc["_id"])  # _id를 id로 변경
        if "password" in user_doc:
            del user_doc["password"]  # 비밀번호 제거
        if "salt" in user_doc:
            del user_doc["salt"]  # salt 제거
        return UserResponse(**user_doc)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """사용자 ID로 조회"""
        collection = self._get_collection()
        user_doc = await collection.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return None
        
        user_doc["id"] = str(user_doc["_id"])  # _id를 id로 변경
        if "password" in user_doc:
            del user_doc["password"]  # 비밀번호 제거
        if "salt" in user_doc:
            del user_doc["salt"]  # salt 제거
        return UserResponse(**user_doc)
    
    def create_tokens(self, user: UserResponse) -> TokenResponse:
        """토큰 쌍 생성"""
        token_data = jwt_manager.create_token_pair(user.id, user.username)
        return TokenResponse(**token_data, user=user)

# 전역 서비스 인스턴스
user_service = UserService() 
import bcrypt
from datetime import datetime
from typing import Optional
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
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """사용자 생성"""
        collection = self._get_collection()
        # 중복 사용자명 확인
        existing_user = await collection.find_one({"username": user_data.username})
        if existing_user:
            raise ValueError("이미 존재하는 사용자명입니다.")
        
        # 비밀번호 해싱
        hashed_password = self.hash_password(user_data.password)
        
        # 사용자 문서 생성
        user_doc = {
            "username": user_data.username,
            "email": user_data.email,
            "nickname": user_data.nickname or user_data.username,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = await collection.insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)  # _id를 id로 변경
        del user_doc["password"]  # 비밀번호 제거
        
        return UserResponse(**user_doc)
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[UserResponse]:
        """사용자 인증"""
        collection = self._get_collection()
        user_doc = await collection.find_one({"username": login_data.username})
        if not user_doc:
            return None
        
        if not self.verify_password(login_data.password, user_doc["password"]):
            return None
        
        # 마지막 로그인 시간 업데이트
        await collection.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        user_doc["id"] = str(user_doc["_id"])  # _id를 id로 변경
        del user_doc["password"]  # 비밀번호 제거
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
        return UserResponse(**user_doc)
    
    def create_tokens(self, user: UserResponse) -> TokenResponse:
        """토큰 쌍 생성"""
        token_data = jwt_manager.create_token_pair(user.id, user.username)
        return TokenResponse(**token_data, user=user)

# 전역 서비스 인스턴스
user_service = UserService() 
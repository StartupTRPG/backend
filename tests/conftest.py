import pytest
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
from datetime import datetime
from unittest.mock import patch
from tests.mock_mongodb import clear_mock_motor

# 테스트 설정
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class TestUser:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.user_id: Optional[str] = None

class E2ETestClient:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.users: Dict[str, TestUser] = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """서버 헬스 체크"""
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """사용자 회원가입"""
        data = {
            "username": username,
            "password": password,
            "email": f"{username}@test.com"
        }
        
        async with self.session.post(f"{BASE_URL}/auth/register", json=data) as response:
            return await response.json()
    
    async def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """사용자 로그인"""
        data = {
            "username": username,
            "password": password
        }
        
        async with self.session.post(f"{BASE_URL}/auth/login", json=data) as response:
            result = await response.json()
            
            if response.status == 200:
                # 사용자 정보 저장
                user = TestUser(username, password)
                user.access_token = result.get("access_token")
                user.refresh_token = result.get("refresh_token")
                self.users[username] = user
                
                # 사용자 ID 가져오기
                await self.get_current_user(username)
            
            return result
    
    async def get_current_user(self, username: str) -> Dict[str, Any]:
        """현재 사용자 정보 조회"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        async with self.session.get(f"{BASE_URL}/auth/me", headers=headers) as response:
            result = await response.json()
            if response.status == 200:
                user.user_id = result.get("id")
            return result
    
    async def refresh_token(self, username: str) -> Dict[str, Any]:
        """토큰 갱신"""
        user = self.users.get(username)
        if not user or not user.refresh_token:
            raise ValueError(f"User {username} not logged in")
        
        data = {"refresh_token": user.refresh_token}
        async with self.session.post(f"{BASE_URL}/auth/refresh", json=data) as response:
            result = await response.json()
            if response.status == 200:
                user.access_token = result.get("access_token")
                user.refresh_token = result.get("refresh_token")
            return result
    
    async def create_room(self, username: str, room_data: Dict[str, Any]) -> Dict[str, Any]:
        """방 생성"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        async with self.session.post(f"{BASE_URL}/rooms", json=room_data, headers=headers) as response:
            return await response.json()
    
    async def list_rooms(self, username: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """방 목록 조회"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        url = f"{BASE_URL}/rooms"
        if params:
            query_params = "&".join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_params}"
        
        async with self.session.get(url, headers=headers) as response:
            return await response.json()
    
    async def get_room(self, username: str, room_id: str) -> Dict[str, Any]:
        """방 정보 조회"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        async with self.session.get(f"{BASE_URL}/rooms/{room_id}", headers=headers) as response:
            return await response.json()
    
    async def get_my_rooms(self, username: str) -> Dict[str, Any]:
        """내가 참가한 방 목록 조회"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        async with self.session.get(f"{BASE_URL}/rooms/my", headers=headers) as response:
            return await response.json()
    
    async def get_chat_history(self, username: str, room_id: str, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        """채팅 기록 조회"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        url = f"{BASE_URL}/chat/room/{room_id}/history?page={page}&limit={limit}"
        async with self.session.get(url, headers=headers) as response:
            return await response.json()
    
    async def delete_account(self, username: str) -> Dict[str, Any]:
        """계정 삭제"""
        user = self.users.get(username)
        if not user or not user.access_token:
            raise ValueError(f"User {username} not logged in")
        
        headers = {"Authorization": f"Bearer {user.access_token}"}
        async with self.session.delete(f"{BASE_URL}/auth/account", headers=headers) as response:
            return await response.json()

@pytest.fixture
async def client():
    client = E2ETestClient()
    await client.__aenter__()
    yield client
    await client.__aexit__(None, None, None)

@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터"""
    return {
        "username": f"testuser_{int(time.time())}",
        "password": "testpassword123",
        "email": f"testuser_{int(time.time())}@test.com"
    }



@pytest.fixture(autouse=True)
async def mock_motor():
    """모든 테스트에서 motor mocking 데이터 초기화"""
    await clear_mock_motor()
    yield
    await clear_mock_motor()

@pytest.fixture
def mock_mongo_collections():
    """모킹된 MongoDB 컬렉션들 반환"""
    from tests.mock_mongodb import get_mock_motor_collection
    
    collections = {
        "users": get_mock_motor_collection("test_db", "users"),
        "rooms": get_mock_motor_collection("test_db", "rooms"),
        "players": get_mock_motor_collection("test_db", "players"),
        "chat": get_mock_motor_collection("test_db", "chat"),
        "profiles": get_mock_motor_collection("test_db", "profiles")
    }
    return collections

@pytest.fixture
async def e2e_client():
    """E2E 테스트용 클라이언트"""
    client = E2ETestClient()
    await client.__aenter__()
    yield client
    await client.__aexit__(None, None, None)
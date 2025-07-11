import pytest
import hashlib
from src.modules.auth.service import AuthService
from src.modules.user.dto import UserCreateRequest, UserLoginRequest
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestAuthService:
    """인증 서비스 유닛 테스트"""
    
    @pytest.fixture
    def auth_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        service = AuthService()
        service.collection = get_mock_motor_collection(db_name, "users")
        return service
    
    def test_hash_password(self, auth_service):
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        assert hashed != password
        assert len(hashed) == 64
        assert hashed == hashlib.sha256(password.encode()).hexdigest()
    
    def test_verify_password(self, auth_service):
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        assert auth_service._verify_password(password, hashed) == True
        assert auth_service._verify_password("wrongpassword", hashed) == False
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service):
        result = await auth_service.register_user("testuser", "testpass123")
        assert result is not None
        assert result.username == "testuser"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, auth_service):
        await auth_service.register_user("testuser", "testpass123")
        with pytest.raises(ValueError, match="이미 사용 중인 사용자명입니다"):
            await auth_service.register_user("testuser", "testpass123")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        await auth_service.register_user("testuser", "testpass123")
        result = await auth_service.authenticate_user("testuser", "testpass123")
        assert result is not None
        assert result.username == "testuser"
        assert result.id is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service):
        await auth_service.register_user("testuser", "testpass123")
        result = await auth_service.authenticate_user("testuser", "wrongpassword")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service):
        result = await auth_service.authenticate_user("nonexistent", "testpass123")
        assert result is None
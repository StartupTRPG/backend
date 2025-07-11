import pytest
import time
from src.modules.auth.service import AuthService
from src.modules.user.service import user_service
from src.modules.user.dto import UserCreateRequest, UserLoginRequest
from src.core.jwt_utils import jwt_manager
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestAuthIntegration:
    """인증 모듈 통합 테스트"""
    
    @pytest.fixture
    def auth_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        service = AuthService()
        service.collection = get_mock_motor_collection(db_name, "users")
        return service

    @pytest.fixture
    def mock_user_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        from src.modules.user.service import user_service
        user_service.collection = get_mock_motor_collection(db_name, "users")
        return user_service
    
    @pytest.mark.asyncio
    async def test_user_registration_and_login_flow(self, auth_service):
        username = f"integration_user_{int(time.time())}"
        password = "testpass123"
        user = await auth_service.register_user(username, password)
        assert user is not None
        assert user.username == username
        authenticated_user = await auth_service.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.username == username
        tokens = await auth_service.login_user(username, password)
        assert tokens is not None
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        access_payload = jwt_manager.verify_token(tokens.access_token)
        assert access_payload is not None
        assert access_payload["username"] == username
        assert access_payload["type"] == "access"
        refresh_payload = jwt_manager.verify_token(tokens.refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["username"] == username
        assert refresh_payload["type"] == "refresh"
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, auth_service):
        username = f"refresh_user_{int(time.time())}"
        password = "testpass123"
        await auth_service.register_user(username, password)
        original_tokens = await auth_service.login_user(username, password)
        # 직접 jwt_manager로 refresh 토큰에서 payload 추출 후 새 토큰 발급
        refresh_payload = jwt_manager.verify_token(original_tokens.refresh_token)
        assert refresh_payload is not None
        assert refresh_payload["username"] == username
        assert refresh_payload["type"] == "refresh"
        # 새 토큰 쌍 발급
        from src.modules.user.dto import UserResponse
        from datetime import datetime
        user = UserResponse(id=refresh_payload["user_id"], username=refresh_payload["username"], email=None, nickname=None, created_at=datetime.utcnow(), last_login=None)
        from src.modules.user.service import user_service
        new_tokens = user_service.create_tokens(user)
        assert new_tokens is not None
        assert new_tokens.refresh_token is not None
        new_access_payload = jwt_manager.verify_token(new_tokens.access_token)
        assert new_access_payload is not None
        assert new_access_payload["username"] == username
    
    @pytest.mark.asyncio
    async def test_user_service_integration(self, mock_user_service):
        user_data = UserCreateRequest(
            username=f"service_user_{int(time.time())}",
            password="testpass123",
            email=f"service_user_{int(time.time())}@test.com"
        )
        user = await mock_user_service.create_user(user_data)
        assert user is not None
        assert user.username == user_data.username
        login_data = UserLoginRequest(
            username=user_data.username,
            password=user_data.password
        )
        authenticated_user = await mock_user_service.authenticate_user(login_data)
        assert authenticated_user is not None
        assert authenticated_user.username == user_data.username
        tokens = mock_user_service.create_tokens(authenticated_user)
        assert tokens is not None
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
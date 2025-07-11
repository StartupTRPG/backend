import pytest
from datetime import datetime
from src.modules.chat.service import ChatService
from src.modules.chat.models import ChatType
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestChatService:
    """채팅 서비스 유닛 테스트"""
    
    @pytest.fixture
    def chat_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        service = ChatService()
        service.collection = get_mock_motor_collection(db_name, "chat")
        return service
    
    @pytest.mark.asyncio
    async def test_save_message_success(self, chat_service):
        result = await chat_service.save_message(
            room_id="test_room_id",
            user_id="test_user_id",
            username="testuser",
            display_name="테스트유저",
            content="안녕하세요!",
            message_type=ChatType.TEXT
        )
        assert result is not None
        assert result.room_id == "test_room_id"
        assert result.username == "testuser"
        assert result.message == "안녕하세요!"
        assert result.message_type == ChatType.TEXT
    
    @pytest.mark.asyncio
    async def test_get_room_messages_success(self, chat_service):
        await chat_service.save_message(
            room_id="test_room_id",
            user_id="user1",
            username="user1",
            display_name="유저1",
            content="첫 번째 메시지",
            message_type=ChatType.TEXT
        )
        await chat_service.save_message(
            room_id="test_room_id",
            user_id="user2",
            username="user2",
            display_name="유저2",
            content="두 번째 메시지",
            message_type=ChatType.TEXT
        )
        result = await chat_service.get_room_messages("test_room_id", page=1, limit=10)
        assert result is not None
        assert result.room_id == "test_room_id"
        assert len(result.messages) == 2
        assert result.total_count == 2
        assert result.page == 1
        assert result.limit == 10
    
    @pytest.mark.asyncio
    async def test_save_system_message(self, chat_service):
        result = await chat_service.save_system_message("test_room_id", "새로운 사용자가 입장했습니다.")
        assert result is not None
        assert result.user_id == "system"
        assert result.username == "시스템"
        assert result.message_type == ChatType.SYSTEM
        assert result.message == "새로운 사용자가 입장했습니다."
    
    @pytest.mark.asyncio
    async def test_delete_room_messages(self, chat_service):
        await chat_service.save_message(
            room_id="test_room_id",
            user_id="user1",
            username="user1",
            display_name="유저1",
            content="메시지",
            message_type=ChatType.TEXT
        )
        await chat_service.save_message(
            room_id="test_room_id",
            user_id="user2",
            username="user2",
            display_name="유저2",
            content="메시지",
            message_type=ChatType.TEXT
        )
        deleted_count = await chat_service.delete_room_messages("test_room_id")
        assert deleted_count == 2
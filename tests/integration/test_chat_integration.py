import pytest
from src.modules.chat.service import chat_service
from src.modules.chat.models import ChatType
from src.core.encryption import encryption_service
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestChatIntegration:
    """채팅 모듈 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_chat_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        chat_service.collection = get_mock_motor_collection(db_name, "chat")
    
    @pytest.mark.asyncio
    async def test_message_save_and_retrieve_flow(self):
        room_id = "test_room_id"
        user_id = "test_user_id"
        username = "testuser"
        display_name = "테스트유저"
        message_content = "안녕하세요! 테스트 메시지입니다."
        saved_message = await chat_service.save_message(
            room_id=room_id,
            user_id=user_id,
            username=username,
            display_name=display_name,
            content=message_content,
            message_type=ChatType.TEXT
        )
        assert saved_message is not None
        assert saved_message.room_id == room_id
        assert saved_message.user_id == user_id
        assert saved_message.username == username
        assert saved_message.message == message_content
        chat_history = await chat_service.get_room_messages(room_id, page=1, limit=10)
        assert chat_history is not None
        assert chat_history.room_id == room_id
        assert len(chat_history.messages) > 0
        found_message = None
        for msg in chat_history.messages:
            if msg.id == saved_message.id:
                found_message = msg
                break
        assert found_message is not None
        assert found_message.message == message_content
        assert found_message.message_type == ChatType.TEXT
    
    @pytest.mark.asyncio
    async def test_system_message_integration(self):
        room_id = "test_room_id"
        system_content = "새로운 사용자가 입장했습니다."
        system_message = await chat_service.save_system_message(room_id, system_content)
        assert system_message is not None
        assert system_message.user_id == "system"
        assert system_message.username == "시스템"
        assert system_message.message_type == ChatType.SYSTEM
        assert system_message.message == system_content
        chat_history = await chat_service.get_room_messages(room_id, page=1, limit=10)
        system_messages = [msg for msg in chat_history.messages if msg.message_type == ChatType.SYSTEM]
        assert len(system_messages) > 0
        assert any(msg.message == system_content for msg in system_messages)
    
    @pytest.mark.asyncio
    async def test_message_pagination(self):
        room_id = "pagination_test_room"
        for i in range(15):
            await chat_service.save_message(
                room_id=room_id,
                user_id=f"user{i}",
                username=f"user{i}",
                display_name=f"유저{i}",
                content=f"메시지 {i}",
                message_type=ChatType.TEXT
            )
        page1 = await chat_service.get_room_messages(room_id, page=1, limit=10)
        assert len(page1.messages) == 10
        assert page1.total_count >= 15
        page2 = await chat_service.get_room_messages(room_id, page=2, limit=10)
        assert len(page2.messages) == 5
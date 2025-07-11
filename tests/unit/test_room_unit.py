import pytest
from src.modules.room.service import RoomService
from src.modules.room.dto import RoomCreateRequest
from src.modules.room.models import RoomStatus, RoomVisibility, PlayerRole
from src.modules.user.dto import UserResponse
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestRoomService:
    """방 서비스 유닛 테스트"""
    
    @pytest.fixture
    def room_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        service = RoomService()
        service.collection = get_mock_motor_collection(db_name, "rooms")
        service.player_collection = get_mock_motor_collection(db_name, "players")
        return service
    
    @pytest.fixture
    def test_user(self):
        return UserResponse(
            id="test_user_id",
            username="testuser",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
    
    @pytest.fixture
    def room_create_request(self):
        return RoomCreateRequest(
            title="테스트 방",
            description="테스트용 방입니다",
            max_players=4,
            visibility=RoomVisibility.PUBLIC,
            password="roompass123",
            game_settings={"game_type": "test"}
        )
    
    def test_hash_password(self, room_service):
        password = "roompass123"
        hashed = room_service._hash_password(password)
        assert hashed != password
        assert len(hashed) == 64
        assert room_service._verify_password(password, hashed) == True
    
    def test_verify_password(self, room_service):
        password = "roompass123"
        hashed = room_service._hash_password(password)
        assert room_service._verify_password(password, hashed) == True
        assert room_service._verify_password("wrongpass", hashed) == False
    
    @pytest.mark.asyncio
    async def test_create_room_success(self, room_service, test_user, room_create_request):
        result = await room_service.create_room(room_create_request, test_user)
        assert result is not None
        assert result.title == room_create_request.title
        assert result.host_id == test_user.id
        assert result.host_username == test_user.username
        assert result.max_players == room_create_request.max_players
        assert result.status == RoomStatus.WAITING
    
    @pytest.mark.asyncio
    async def test_get_room_success(self, room_service, test_user, room_create_request):
        created = await room_service.create_room(room_create_request, test_user)
        result = await room_service.get_room(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.title == created.title
        assert len(result.players) == 1
        assert result.players[0].role == PlayerRole.HOST
    
    @pytest.mark.asyncio
    async def test_get_room_not_found(self, room_service):
        result = await room_service.get_room("nonexistent_room_id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_rooms_with_filters(self, room_service, test_user, room_create_request):
        await room_service.create_room(room_create_request, test_user)
        result = await room_service.list_rooms(
            status=RoomStatus.WAITING,
            visibility=RoomVisibility.PUBLIC,
            search="테스트",
            page=1,
            limit=10
        )
        assert len(result) >= 1
        assert any(r.title == "테스트 방" for r in result)
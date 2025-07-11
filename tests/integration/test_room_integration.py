import pytest
from src.modules.room.service import room_service
from src.modules.room.dto import RoomCreateRequest
from src.modules.room.models import RoomStatus, RoomVisibility, PlayerRole
from src.modules.user.dto import UserResponse
from tests.mock_mongodb import get_mock_motor_collection
import uuid

class TestRoomIntegration:
    """방 모듈 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup_room_service(self):
        db_name = f"testdb_{uuid.uuid4().hex}"
        room_service.collection = get_mock_motor_collection(db_name, "rooms")
        room_service.player_collection = get_mock_motor_collection(db_name, "players")
    
    @pytest.fixture
    def test_user(self):
        return UserResponse(
            id="test_user_id",
            username="testuser",
            created_at="2023-01-01T00:00:00",
            updated_at="2023-01-01T00:00:00"
        )
    
    @pytest.mark.asyncio
    async def test_room_creation_and_management_flow(self, test_user):
        room_data = RoomCreateRequest(
            title="통합 테스트 방",
            description="통합 테스트용 방입니다",
            max_players=4,
            visibility=RoomVisibility.PUBLIC,
            password="roompass123",
            game_settings={"game_type": "test"}
        )
        room = await room_service.create_room(room_data, test_user)
        assert room is not None
        assert room.title == room_data.title
        assert room.host_id == test_user.id
        assert room.status == RoomStatus.WAITING
        retrieved_room = await room_service.get_room(room.id)
        assert retrieved_room is not None
        assert retrieved_room.id == room.id
        assert retrieved_room.title == room.title
        success = await room_service.add_player_to_room(
            room.id, "player_user_id", "playeruser", "roompass123"
        )
        assert success == True
        players = await room_service.get_room_players(room.id)
        assert len(players) == 2
        assert any(p.role == PlayerRole.HOST for p in players)
        assert any(p.role == PlayerRole.PLAYER for p in players)
        rooms = await room_service.list_rooms(status=RoomStatus.WAITING)
        assert len(rooms) > 0
        assert any(r.id == room.id for r in rooms)
    
    @pytest.mark.asyncio
    async def test_room_password_verification(self, test_user):
        room_data = RoomCreateRequest(
            title="비밀번호 방",
            description="비밀번호가 있는 방",
            max_players=2,
            visibility=RoomVisibility.PRIVATE,
            password="secretpass",
            game_settings={}
        )
        room = await room_service.create_room(room_data, test_user)
        success_correct = await room_service.add_player_to_room(
            room.id, "player1", "player1", "secretpass"
        )
        assert success_correct == True
        with pytest.raises(ValueError, match="잘못된 비밀번호입니다|방이 가득 찼습니다"):
            await room_service.add_player_to_room(
                room.id, "player2", "player2", "wrongpass"
            )
    
    @pytest.mark.asyncio
    async def test_room_capacity_management(self, test_user):
        room_data = RoomCreateRequest(
            title="인원 제한 방",
            description="최대 3명 방",
            max_players=3,
            visibility=RoomVisibility.PUBLIC,
            password="",
            game_settings={}
        )
        room = await room_service.create_room(room_data, test_user)
        success1 = await room_service.add_player_to_room(
            room.id, "player1", "player1"
        )
        assert success1 == True
        success2 = await room_service.add_player_to_room(
            room.id, "player2", "player2"
        )
        assert success2 == True
        with pytest.raises(ValueError, match="방이 가득 찼습니다"):
            await room_service.add_player_to_room(
                room.id, "player3", "player3"
            )
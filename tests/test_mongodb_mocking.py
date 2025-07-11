import pytest
from datetime import datetime
from tests.mock_mongodb import get_mock_motor_collection

class TestMongoDBMocking:
    """mongomock-motor 기반 motor mocking 테스트"""

    @pytest.mark.asyncio
    async def test_motor_insert_and_find(self):
        col = get_mock_motor_collection("testdb", "users")
        doc = {"username": "testuser", "email": "test@example.com", "created_at": datetime.utcnow()}
        result = await col.insert_one(doc)
        assert result.inserted_id
        found = await col.find_one({"username": "testuser"})
        assert found["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_motor_find_many(self):
        col = get_mock_motor_collection("testdb", "rooms")
        await col.insert_one({"title": "방1", "host": "user1"})
        await col.insert_one({"title": "방2", "host": "user2"})
        await col.insert_one({"title": "방3", "host": "user3"})
        docs = await col.find({}).to_list(length=None)
        assert len(docs) == 3

    @pytest.mark.asyncio
    async def test_motor_update(self):
        col = get_mock_motor_collection("testdb", "chat")
        await col.insert_one({"room": "r1", "msg": "hello"})
        await col.update_one({"room": "r1"}, {"$set": {"msg": "bye"}})
        found = await col.find_one({"room": "r1"})
        assert found["msg"] == "bye"

    @pytest.mark.asyncio
    async def test_motor_delete(self):
        col = get_mock_motor_collection("testdb", "players")
        await col.insert_one({"user": "u1"})
        await col.insert_one({"user": "u2"})
        await col.delete_one({"user": "u1"})
        docs = await col.find({}).to_list(length=None)
        assert len(docs) == 1
        assert docs[0]["user"] == "u2"

    @pytest.mark.asyncio
    async def test_motor_count(self):
        col = get_mock_motor_collection("testdb", "profiles")
        await col.insert_one({"user": "u1"})
        await col.insert_one({"user": "u2"})
        count = await col.count_documents({})
        assert count == 2 
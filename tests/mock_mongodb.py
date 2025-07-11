from mongomock_motor import AsyncMongoMockClient

# 테스트에서 사용할 모킹 클라이언트 인스턴스
mock_motor_client = AsyncMongoMockClient()

def get_mock_motor_collection(db_name: str, collection_name: str):
    """motor 스타일의 모킹 컬렉션 반환"""
    return mock_motor_client[db_name][collection_name]

async def clear_mock_motor():
    """모든 모킹 데이터 초기화"""
    # mongomock-motor는 drop_database로 초기화 가능
    db_names = await mock_motor_client.list_database_names()
    for db_name in db_names:
        await mock_motor_client.drop_database(db_name) 
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class SocketEventDoc(BaseModel):
    """Socket 이벤트 문서"""
    event: str = Field(..., description="이벤트 이름")
    description: str = Field(..., description="이벤트 설명")
    direction: str = Field(..., description="방향 (client->server, server->client, bidirectional)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="파라미터")
    example_request: Dict[str, Any] = Field(default_factory=dict, description="요청 예시")
    example_response: Dict[str, Any] = Field(default_factory=dict, description="응답 예시")
    authentication_required: bool = Field(default=True, description="인증 필요 여부")

# Socket.IO 이벤트 문서 정의
SOCKET_EVENTS_DOCS: List[SocketEventDoc] = [
    # 인증 관련
    SocketEventDoc(
        event="connect",
        description="클라이언트 연결 (JWT 토큰 필요)",
        direction="client->server",
        parameters={
            "auth": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "JWT 액세스 토큰"}
                },
                "required": ["token"]
            }
        },
        example_request={
            "auth": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        },
        example_response={
            "user_id": "user_123",
            "username": "사용자명",
            "message": "성공적으로 연결되었습니다."
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="disconnect",
        description="클라이언트 연결 해제",
        direction="client->server",
        parameters={},
        example_request={},
        example_response={},
        authentication_required=True
    ),
    
    # 방 관련
    SocketEventDoc(
        event="join_room",
        description="방 입장",
        direction="client->server",
        parameters={
            "room_id": {"type": "string", "description": "방 ID"},
            "password": {"type": "string", "description": "방 비밀번호 (선택사항)"}
        },
        example_request={
            "room_id": "room_123",
            "password": "1234"
        },
        example_response={
            "room_id": "room_123",
            "room_name": "게임방",
            "message": "게임방에 입장했습니다."
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="leave_room",
        description="방 나가기",
        direction="client->server",
        parameters={
            "room_id": {"type": "string", "description": "방 ID (선택사항, 현재 방에서 나가기)"}
        },
        example_request={
            "room_id": "room_123"
        },
        example_response={
            "room_id": "room_123",
            "message": "방에서 나갔습니다."
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="get_room_users",
        description="방 사용자 목록 조회",
        direction="client->server",
        parameters={
            "room_id": {"type": "string", "description": "방 ID (선택사항, 현재 방)"}
        },
        example_request={
            "room_id": "room_123"
        },
        example_response={
            "room_id": "room_123",
            "users": [
                {
                    "user_id": "user_123",
                    "username": "사용자1",
                    "display_name": "표시명1",
                    "is_host": True,
                    "joined_at": "2024-01-01T12:00:00Z"
                }
            ],
            "total_count": 1
        },
        authentication_required=True
    ),
    
    # 채팅 관련
    SocketEventDoc(
        event="send_message",
        description="채팅 메시지 전송 (암호화되어 저장)",
        direction="client->server",
        parameters={
            "message": {"type": "string", "description": "메시지 내용 (최대 1000자)"}
        },
        example_request={
            "message": "안녕하세요!"
        },
        example_response={
            "id": "msg_123",
            "user_id": "user_123",
            "username": "사용자명",
            "display_name": "표시명",
            "message": "안녕하세요!",
            "timestamp": "2024-01-01T12:00:00Z",
            "message_type": "text",
            "encrypted": True
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="get_chat_history",
        description="채팅 기록 조회 (자동 복호화)",
        direction="client->server",
        parameters={
            "room_id": {"type": "string", "description": "방 ID"},
            "page": {"type": "integer", "description": "페이지 번호 (기본값: 1)"},
            "limit": {"type": "integer", "description": "페이지당 메시지 수 (기본값: 50, 최대: 100)"}
        },
        example_request={
            "room_id": "room_123",
            "page": 1,
            "limit": 50
        },
        example_response={
            "room_id": "room_123",
            "messages": [
                {
                    "id": "msg_123",
                    "user_id": "user_123",
                    "username": "사용자명",
                    "display_name": "표시명",
                    "message": "안녕하세요!",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "message_type": "text",
                    "encrypted": True
                }
            ],
            "total_count": 1,
            "page": 1,
            "limit": 50
        },
        authentication_required=True
    ),
    
    # 서버에서 클라이언트로 전송되는 이벤트들
    SocketEventDoc(
        event="new_message",
        description="새 메시지 수신 (실시간)",
        direction="server->client",
        parameters={},
        example_request={},
        example_response={
            "id": "msg_123",
            "user_id": "user_123",
            "username": "사용자명",
            "display_name": "표시명",
            "message": "안녕하세요!",
            "timestamp": "2024-01-01T12:00:00Z",
            "message_type": "text",
            "encrypted": True
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="user_joined",
        description="사용자 입장 알림",
        direction="server->client",
        parameters={},
        example_request={},
        example_response={
            "user_id": "user_123",
            "username": "사용자명",
            "display_name": "표시명",
            "message": "사용자명님이 입장했습니다.",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="user_left",
        description="사용자 퇴장 알림",
        direction="server->client",
        parameters={},
        example_request={},
        example_response={
            "user_id": "user_123",
            "username": "사용자명",
            "display_name": "표시명",
            "message": "사용자명님이 나갔습니다.",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        authentication_required=True
    ),
    
    SocketEventDoc(
        event="error",
        description="에러 메시지",
        direction="server->client",
        parameters={},
        example_request={},
        example_response={
            "message": "에러 메시지"
        },
        authentication_required=False
    ),
    
    SocketEventDoc(
        event="connect_success",
        description="연결 성공 알림",
        direction="server->client",
        parameters={},
        example_request={},
        example_response={
            "user_id": "user_123",
            "username": "사용자명",
            "message": "성공적으로 연결되었습니다."
        },
        authentication_required=True
    )
]

def get_socket_events_documentation() -> Dict[str, Any]:
    """Socket.IO 이벤트 문서 반환"""
    return {
        "socket_io_events": {
            "connection_url": "ws://localhost:8000/socket.io/",
            "authentication": {
                "type": "JWT Token",
                "description": "연결 시 auth 객체에 JWT 토큰 포함 필요",
                "example": {
                    "auth": {
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                    }
                }
            },
            "events": [event.dict() for event in SOCKET_EVENTS_DOCS]
        }
    } 
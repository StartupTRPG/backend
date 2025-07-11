from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any
from src.core.socket import get_socket_events_documentation

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """커스텀 OpenAPI 스키마 생성"""
    if app.openapi_schema:
        return app.openapi_schema
    
    # 기본 OpenAPI 스키마 생성
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Socket.IO 문서 추가
    socket_docs = get_socket_events_documentation()
    
    # OpenAPI 스키마에 Socket.IO 정보 추가
    openapi_schema["info"]["x-socket-io"] = socket_docs["socket_io_events"]
    
    # 커스텀 섹션 추가
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # Socket.IO 이벤트를 가짜 경로로 추가 (문서화 목적)
    socket_paths = {}
    
    for event in socket_docs["socket_io_events"]["events"]:
        if event["direction"] == "client->server":
            path_name = f"/socket.io/{event['event']}"
            socket_paths[path_name] = {
                "post": {
                    "tags": ["Socket.IO Events"],
                    "summary": event["description"],
                    "description": f"""
**Socket.IO 이벤트**: `{event['event']}`
**방향**: {event['direction']}
**인증 필요**: {'Yes' if event['authentication_required'] else 'No'}

**연결 방법**:
```javascript
const socket = io('ws://localhost:8000', {{
    auth: {{
        token: 'your-jwt-token'
    }}
}});

socket.emit('{event['event']}', {event['example_request']});
```

**응답 수신**:
```javascript
socket.on('{event['event']}_response', (data) => {{
    console.log(data);
}});
```
                    """,
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": event["parameters"] if event["parameters"] else {},
                                    "example": event["example_request"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "example": event["example_response"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        elif event["direction"] == "server->client":
            path_name = f"/socket.io/{event['event']}"
            socket_paths[path_name] = {
                "get": {
                    "tags": ["Socket.IO Events (Server→Client)"],
                    "summary": event["description"],
                    "description": f"""
**Socket.IO 이벤트**: `{event['event']}`
**방향**: {event['direction']}
**인증 필요**: {'Yes' if event['authentication_required'] else 'No'}

**수신 방법**:
```javascript
socket.on('{event['event']}', (data) => {{
    console.log(data);
    // 응답 데이터 처리
}});
```

**예시 데이터**:
```json
{event['example_response']}
```
                    """,
                    "responses": {
                        "200": {
                            "description": "Event Data",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "example": event["example_response"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
    
    # 기존 경로와 Socket.IO 경로 병합
    if "paths" not in openapi_schema:
        openapi_schema["paths"] = {}
    
    openapi_schema["paths"].update(socket_paths)
    
    # 보안 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "SocketAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Socket.IO 연결 시 auth 객체에 JWT 토큰 포함"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 
from pydantic import BaseModel


class LogoutResponse(BaseModel):
    """로그아웃 응답 모델"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "instructions": {
                        "client_action": "토큰을 로컬 저장소에서 삭제하고 Socket.IO 연결을 해제하세요."
                    }
                },
                "message": "로그아웃이 완료되었습니다. 클라이언트에서 토큰을 삭제해주세요.",
                "success": True
            }
        } 
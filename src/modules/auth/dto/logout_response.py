from pydantic import BaseModel
from typing import Dict, Any


class LogoutData(BaseModel):
    """로그아웃 응답 데이터"""
    instructions: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "instructions": {
                    "client_action": "액세스 토큰을 로컬 저장소에서 삭제하고 Socket.IO 연결을 해제하세요."
                }
            }
        }


class LogoutResponse(BaseModel):
    """Logout response model"""
    data: LogoutData
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "instructions": {
                        "client_action": "액세스 토큰을 로컬 저장소에서 삭제하고 Socket.IO 연결을 해제하세요."
                    }
                },
                "message": "Logout completed successfully.",
                "success": True
            }
        } 
from pydantic import BaseModel, Field


class RoomOperationData(BaseModel):
    """방 작업 응답 데이터"""
    room_id: str = Field(..., description="방 ID")
    operation: str = Field(..., description="수행된 작업")
    timestamp: str = Field(..., description="작업 수행 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_id": "507f1f77bcf86cd799439011",
                "operation": "start_game",
                "timestamp": "2024-01-01T12:30:00"
            }
        }


class RoomOperationResponse(BaseModel):
    """방 작업 응답 모델"""
    data: RoomOperationData = Field(..., description="작업 데이터")
    message: str = Field(..., description="응답 메시지")
    success: bool = Field(..., description="작업 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "room_id": "507f1f77bcf86cd799439011",
                    "operation": "start_game",
                    "timestamp": "2024-01-01T12:30:00"
                },
                "message": "게임이 시작되었습니다.",
                "success": True
            }
        } 
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """공통 API 응답 모델"""
    data: T
    message: str
    success: bool = Field(default=True, description="요청 성공 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {},
                "message": "요청이 성공적으로 처리되었습니다.",
                "success": True
            }
        }

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    message: str
    success: bool = Field(default=False, description="요청 성공 여부")
    error_code: Optional[str] = Field(default=None, description="에러 코드")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "요청 처리 중 오류가 발생했습니다.",
                "success": False,
                "error_code": "INTERNAL_ERROR"
            }
        } 
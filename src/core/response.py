from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Common API response model"""
    data: T
    message: str
    success: bool = Field(default=True, description="Request success status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {},
                "message": "Request processed successfully.",
                "success": True
            }
        }

class ErrorResponse(BaseModel):
    """Error response model"""
    message: str
    success: bool = Field(default=False, description="Request success status")
    error_code: Optional[str] = Field(default=None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "An error occurred while processing the request.",
                "success": False,
                "error_code": "INTERNAL_ERROR"
            }
        } 
from pydantic import BaseModel


class DeleteAccountResponse(BaseModel):
    """계정 삭제 응답 모델"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "instructions": {
                        "client_action": "모든 토큰을 삭제하고 로그인 페이지로 이동하세요."
                    }
                },
                "message": "계정이 성공적으로 삭제되었습니다.",
                "success": True
            }
        } 
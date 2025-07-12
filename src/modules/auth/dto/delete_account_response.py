from pydantic import BaseModel


class DeleteAccountResponse(BaseModel):
    """Account deletion response model"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "instructions": {
                        "client_action": "Delete all tokens and navigate to login page."
                    }
                },
                "message": "Account deleted successfully.",
                "success": True
            }
        } 
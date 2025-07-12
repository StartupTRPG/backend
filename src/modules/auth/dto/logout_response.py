from pydantic import BaseModel


class LogoutResponse(BaseModel):
    """Logout response model"""
    data: dict
    message: str
    success: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "instructions": {
                        "client_action": "Delete token from local storage and disconnect Socket.IO connection."
                    }
                },
                "message": "Logout completed. Please delete the token from the client.",
                "success": True
            }
        } 
from pydantic import BaseModel

class RoomJoinRequest(BaseModel):
    """방 입장 요청 DTO (Socket.IO용)"""
    room_id: str 
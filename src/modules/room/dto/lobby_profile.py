from pydantic import BaseModel

class LobbyProfileCreate(BaseModel):
    """로비 프로필 생성 요청 (이름만)"""
    character_name: str 
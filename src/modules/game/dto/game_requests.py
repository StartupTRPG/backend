from pydantic import BaseModel
from typing import List

class Player(BaseModel):
    id: str
    name: str

class CreateGameRequest(BaseModel):
    room_id: str
    players: List[Player] 
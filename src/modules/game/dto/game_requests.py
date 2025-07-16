from pydantic import BaseModel
from typing import List, Dict

class Player(BaseModel):
    id: str
    name: str
    role: str = None  # llm-backend dto에 맞춰 role 추가

class PlayerContext(BaseModel):
    id: str
    name: str
    role: str
    context: Dict[str, str]

class AgendaOption(BaseModel):
    id: str
    text: str
    impact_summary: str

class Agenda(BaseModel):
    id: str
    name: str
    description: str
    options: List[AgendaOption]

class TaskOption(BaseModel):
    id: str
    text: str
    impact_summary: str

class Task(BaseModel):
    id: str
    name: str
    description: str
    options: List[TaskOption]

class OvertimeTaskOption(BaseModel):
    id: str
    text: str
    impact_summary: str

class OvertimeTask(BaseModel):
    id: str
    type: str
    name: str
    description: str
    options: List[OvertimeTaskOption]

class CreateGameRequest(BaseModel):
    room_id: str
    players: List[Player]

class CreateContextRequest(BaseModel):
    max_turn: int
    story: str
    player_list: List[Player]

class CreateAgendaRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext]

class CreateTaskRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext]

class CreateOvertimeRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext]

class UpdateContextRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext]
    agenda_list: List[Agenda]
    task_list: Dict[str, List[Task]]
    overtime_task_list: Dict[str, List[OvertimeTask]]

class ExplanationRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext]

class ResultRequest(BaseModel):
    company_context: Dict[str, str]
    player_context_list: List[PlayerContext] 
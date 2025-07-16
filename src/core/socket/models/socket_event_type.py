from enum import Enum

class SocketEventType(str, Enum):
    """Socket 이벤트 타입"""
    # 인증 관련
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    CONNECT_SUCCESS = "connect_success"
    CONNECT_FAILED = "connect_failed"
    
    # 방 관련
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_DELETED = "room_deleted"
    
    # 게임 관련
    START_GAME = "start_game"
    FINISH_GAME = "finish_game"
    
    # LLM 게임 관련
    CREATE_GAME = "create_game"
    CREATE_CONTEXT = "create_context"
    CREATE_AGENDA = "create_agenda"
    AGENDA_LOADING_STARTED = "agenda_loading_started"
    CREATE_TASK = "create_task"
    CREATE_OVERTIME = "create_overtime"
    UPDATE_CONTEXT = "update_context"
    CREATE_EXPLANATION = "create_explanation"
    CALCULATE_RESULT = "calculate_result"
    GET_GAME_PROGRESS = "get_game_progress"
    GAME_PROGRESS_UPDATED = "game_progress_updated"
    
    # 아젠다 투표 관련
    VOTE_AGENDA = "vote_agenda"
    AGENDA_VOTE_BROADCAST = "agenda_vote_broadcast"
    AGENDA_VOTE_COMPLETED = "agenda_vote_completed"
    AGENDA_NAVIGATE = "agenda_navigate"  # 아젠다 네비게이션 (다음/이전)
    
    # 태스크 완료 관련
    TASK_COMPLETED = "task_completed"  # 태스크 완료 알림
    TASK_COMPLETED_BROADCAST = "task_completed_broadcast"  # 태스크 완료 브로드캐스트
    TASK_NAVIGATE = "task_navigate"  # 태스크 네비게이션 (다음 단계로)
    
    # 태스크 생성 관련
    TASK_CREATED = "task_created"
    
    # 채팅 관련
    LOBBY_MESSAGE = "lobby_message"
    SYSTEM_MESSAGE = "system_message"
    GAME_MESSAGE = "game_message"
    
    # 공통
    ERROR = "error"
    FORCE_DISCONNECT = "force_disconnect"
    READY = "ready"  # 플레이어 레디/언레디
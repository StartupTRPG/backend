from typing import Dict, Optional
import logging
from .interfaces import SocketEventType
# 순환 import 방지를 위해 직접 strategy.py에서 import
from .strategy import (
    SocketMessageStrategy,
    AuthConnectStrategy,
    AuthDisconnectStrategy,
    RoomJoinStrategy,
    RoomLeaveStrategy,
    StartGameStrategy,
    FinishGameStrategy,
    LobbyMessageStrategy,
    GameMessageStrategy,
    SystemMessageStrategy,
    ReadyStrategy,
    # 게임 관련 전략들 추가
    CreateGameStrategy,
    CreateContextStrategy,
    CreateAgendaStrategy,
    CreateTaskStrategy,
    CreateOvertimeStrategy,
    UpdateContextStrategy,
    CreateExplanationStrategy,
    CalculateResultStrategy,
    GetGameProgressStrategy,
    # 아젠다 투표 전략 추가
    AgendaVoteStrategy,
    # 아젠다 네비게이션 전략 추가
    AgendaNavigateStrategy,
    # 태스크 완료 전략 추가
    TaskCompletedStrategy,
    # 태스크 네비게이션 전략 추가
    TaskNavigateStrategy,
)

logger = logging.getLogger(__name__)

class SocketMessageStrategyFactory:
    """Socket message strategy factory"""
    
    def __init__(self) -> None:
        self._strategies: Dict[SocketEventType, SocketMessageStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self) -> None:
        """Initialize strategies"""
        strategies = [
            AuthConnectStrategy(),
            AuthDisconnectStrategy(),
            RoomJoinStrategy(),
            RoomLeaveStrategy(),
            StartGameStrategy(),
            FinishGameStrategy(),
            LobbyMessageStrategy(),
            GameMessageStrategy(),
            SystemMessageStrategy(),
            ReadyStrategy(),
            # 게임 관련 전략들 추가
            CreateGameStrategy(),
            CreateContextStrategy(),
            CreateAgendaStrategy(),
            CreateTaskStrategy(),
            CreateOvertimeStrategy(),
            UpdateContextStrategy(),
            CreateExplanationStrategy(),
            CalculateResultStrategy(),
            GetGameProgressStrategy(),
            # 아젠다 투표 전략 추가
            AgendaVoteStrategy(),
            # 아젠다 네비게이션 전략 추가
            AgendaNavigateStrategy(),
            # 태스크 완료 전략 추가
            TaskCompletedStrategy(),
            # 태스크 네비게이션 전략 추가
            TaskNavigateStrategy(),
        ]
        
        for strategy in strategies:
            self._strategies[strategy.get_event_type()] = strategy
            logger.debug(f"Registered strategy for {strategy.get_event_type()}")
    
    def get_strategy(self, event_type: SocketEventType) -> Optional[SocketMessageStrategy]:
        """Get strategy by event type"""
        strategy = self._strategies.get(event_type)
        if not strategy:
            logger.warning(f"No strategy found for event type: {event_type}")
            return None
        
        logger.debug(f"Retrieved strategy for {event_type}: {strategy.__class__.__name__}")
        return strategy
    
    def register_strategy(self, event_type: SocketEventType, strategy: SocketMessageStrategy) -> None:
        """Register new strategy"""
        self._strategies[event_type] = strategy
        logger.info(f"Registered new strategy for {event_type}: {strategy.__class__.__name__}")
    
    def get_supported_event_types(self) -> list:
        """Get list of supported event types"""
        return list(self._strategies.keys())
    
    def has_strategy(self, event_type: SocketEventType) -> bool:
        """Check if strategy exists for a specific event type"""
        return event_type in self._strategies

# 싱글톤 팩토리 인스턴스
_factory_instance = None

def get_strategy_factory() -> SocketMessageStrategyFactory:
    """Get singleton strategy factory instance"""
    if not hasattr(get_strategy_factory, '_instance'):
        get_strategy_factory._instance = SocketMessageStrategyFactory()
        logger.info("Socket message strategy factory initialized")
    return get_strategy_factory._instance 
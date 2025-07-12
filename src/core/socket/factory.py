from typing import Dict, Optional
import logging
from .interfaces import SocketEventType
from .strategy import (
    SocketMessageStrategy,
    AuthConnectStrategy,
    AuthDisconnectStrategy,
    RoomJoinStrategy,
    RoomLeaveStrategy,
    RoomUsersStrategy,
    ChatSendMessageStrategy,
    ChatHistoryStrategy
)

logger = logging.getLogger(__name__)

class SocketMessageStrategyFactory:
    """Socket message strategy factory"""
    
    def __init__(self):
        self._strategies: Dict[SocketEventType, SocketMessageStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize strategies"""
        strategies = [
            AuthConnectStrategy(),
            AuthDisconnectStrategy(),
            RoomJoinStrategy(),
            RoomLeaveStrategy(),
            RoomUsersStrategy(),
            ChatSendMessageStrategy(),
            ChatHistoryStrategy()
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
    
    def register_strategy(self, event_type: SocketEventType, strategy: SocketMessageStrategy):
        """Register new strategy"""
        self._strategies[event_type] = strategy
        logger.info(f"Registered new strategy for {event_type}: {strategy.__class__.__name__}")
    
    def get_supported_event_types(self) -> list[SocketEventType]:
        """Return list of supported event types"""
        return list(self._strategies.keys())
    
    def has_strategy(self, event_type: SocketEventType) -> bool:
        """Check if strategy exists for a specific event type"""
        return event_type in self._strategies

# 싱글톤 팩토리 인스턴스
_factory_instance = None

def get_strategy_factory() -> SocketMessageStrategyFactory:
    """Return strategy factory singleton instance"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = SocketMessageStrategyFactory()
        logger.info("Socket message strategy factory initialized")
    return _factory_instance 
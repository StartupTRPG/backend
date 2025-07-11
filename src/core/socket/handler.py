from typing import Dict, Any, Optional
import logging
from .interfaces import BaseSocketMessage, SocketEventType
from .factory import get_strategy_factory

logger = logging.getLogger(__name__)

class SocketMessageHandler:
    """소켓 메시지 핸들러 - 전략 패턴과 팩토리 패턴 적용"""
    
    def __init__(self, sio):
        self.sio = sio
        self.strategy_factory = get_strategy_factory()
        logger.info(f"Socket message handler initialized with {len(self.strategy_factory.get_supported_event_types())} strategies")
    
    async def handle_message(self, event_type: SocketEventType, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """메시지 처리 - 전략 패턴 적용"""
        try:
            # 팩토리에서 적절한 전략 가져오기
            strategy = self.strategy_factory.get_strategy(event_type)
            if not strategy:
                logger.error(f"No strategy found for event type: {event_type}")
                await self._send_error(sid, f"지원하지 않는 이벤트 타입입니다: {event_type}")
                return None
            
            # 전략을 통한 메시지 처리 (세션 검증은 전략 내부에서 처리)
            logger.debug(f"Processing {event_type} with strategy: {strategy.__class__.__name__}")
            result = await strategy.handle(self.sio, sid, data)
            
            if result:
                logger.info(f"Successfully processed {event_type} for sid: {sid}")
            
            return result
            
        except Exception as e:
            logger.error(f"Message handling error for {event_type}: {str(e)}")
            await self._send_error(sid, "메시지 처리 중 오류가 발생했습니다.")
            return None
    
    async def _send_error(self, sid: str, message: str):
        """에러 메시지 전송"""
        await self.sio.emit('error', {'message': message}, room=sid)
    
    async def _send_success(self, sid: str, data: Dict[str, Any]):
        """성공 메시지 전송"""
        await self.sio.emit('success', data, room=sid)
    
    def get_supported_event_types(self) -> list[SocketEventType]:
        """지원하는 이벤트 타입 목록 반환"""
        return self.strategy_factory.get_supported_event_types()
    
    def register_custom_strategy(self, event_type: SocketEventType, strategy):
        """사용자 정의 전략 등록"""
        self.strategy_factory.register_strategy(event_type, strategy)
        logger.info(f"Registered custom strategy for {event_type}")
    
    def has_strategy(self, event_type: SocketEventType) -> bool:
        """특정 이벤트 타입에 대한 전략 존재 여부 확인"""
        return self.strategy_factory.has_strategy(event_type) 
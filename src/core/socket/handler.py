from typing import Dict, Any, Optional
import logging
from .interfaces import BaseSocketMessage, SocketEventType
from .factory import get_strategy_factory

logger = logging.getLogger(__name__)

def log_socket_message(level: str, message: str, **kwargs):
    """소켓 메시지 전용 로깅 함수"""
    colors = {
        'INFO': '\033[94m',      # 파란색
        'SUCCESS': '\033[92m',   # 초록색
        'WARNING': '\033[93m',   # 노란색
        'ERROR': '\033[91m',     # 빨간색
    }
    
    color = colors.get(level, '')
    reset = '\033[0m'
    
    # 한 줄로 모든 정보 정리
    if kwargs:
        details = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        log_msg = f"{color}[SOCKET] {message} {details}{reset}"
    else:
        log_msg = f"{color}[SOCKET] {message}{reset}"
    
    if level == 'ERROR':
        logger.error(log_msg)
    elif level == 'WARNING':
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

class SocketMessageHandler:
    """Socket message handler - uses strategy and factory patterns"""
    
    def __init__(self, sio):
        self.sio = sio
        self.strategy_factory = get_strategy_factory()
        logger.info(f"Socket message handler initialized with {len(self.strategy_factory.get_supported_event_types())} strategies")
    
    async def handle_message(self, event_type: SocketEventType, sid: str, data: Dict[str, Any]) -> Optional[BaseSocketMessage]:
        """Handle message - applies strategy pattern"""
        log_socket_message('INFO', '수신', event=event_type, sid=sid[:8])
        
        try:
            strategy = self.strategy_factory.get_strategy(event_type)
            if not strategy:
                log_socket_message('ERROR', '지원하지 않는 이벤트', event=event_type)
                await self._send_error(sid, f"Unsupported event type: {event_type}")
                return None
            
            result = await strategy.handle(self.sio, sid, data)
            
            if result:
                log_socket_message('SUCCESS', '완료', event=event_type, sid=sid[:8])
            else:
                log_socket_message('WARNING', '실패', event=event_type, sid=sid[:8])
            
            return result
            
        except Exception as e:
            log_socket_message('ERROR', '오류', event=event_type, sid=sid[:8], error=str(e)[:30])
            await self._send_error(sid, "An error occurred while handling the message.")
            return None
    
    async def _send_error(self, sid: str, message: str):
        """Send error message"""
        log_socket_message('ERROR', '전송', event='error', sid=sid[:8], msg=message[:50])
        await self.sio.emit('error', {'message': message}, room=sid)
    
    async def _send_success(self, sid: str, data: Dict[str, Any]):
        """성공 메시지 전송"""
        log_socket_message('SUCCESS', '전송', event='success', sid=sid[:8], data=str(data)[:50])
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
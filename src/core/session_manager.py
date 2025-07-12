import logging
from typing import Dict, Optional, Set
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class SessionManager:
    """사용자 세션 관리자 - 중복 로그인 및 여러 방 접속 방지"""
    
    def __init__(self):
        # user_id -> sid 매핑 (한 사용자는 하나의 세션만)
        self.user_sessions: Dict[str, str] = {}
        
        # sid -> user_id 매핑 (세션 정보)
        self.session_users: Dict[str, str] = {}
        
        # user_id -> room_id 매핑 (한 사용자는 하나의 방만)
        self.user_rooms: Dict[str, str] = {}
        
        # room_id -> Set[user_id] 매핑 (방에 있는 사용자들)
        self.room_users: Dict[str, Set[str]] = {}
        
        # 세션 타임아웃 관리 (sid -> 마지막 활동 시간)
        self.session_activity: Dict[str, datetime] = {}
        
        # 락 (동시성 제어)
        self._lock = asyncio.Lock()
    
    async def register_session(self, sid: str, user_id: str) -> bool:
        """새로운 세션 등록 - 중복 로그인 방지"""
        async with self._lock:
            try:
                # 이미 다른 세션에서 로그인된 사용자인지 확인
                if user_id in self.user_sessions:
                    old_sid = self.user_sessions[user_id]
                    logger.warning(f"User {user_id} already has active session {old_sid}, forcing disconnect")
                    
                    # 기존 세션 강제 해제
                    await self._force_disconnect_session(old_sid, "다른 디바이스에서 로그인되었습니다.")
                
                # 새 세션 등록
                self.user_sessions[user_id] = sid
                self.session_users[sid] = user_id
                self.session_activity[sid] = datetime.utcnow()
                
                logger.info(f"New session registered: user_id={user_id}, sid={sid}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register session: {str(e)}")
                return False
    
    async def unregister_session(self, sid: str) -> bool:
        """세션 해제"""
        async with self._lock:
            try:
                user_id = self.session_users.get(sid)
                if not user_id:
                    logger.warning(f"Session {sid} not found for unregistration")
                    return False
                
                # 사용자 세션 정보 제거
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                
                # 세션 정보 제거
                del self.session_users[sid]
                
                # 활동 시간 제거
                if sid in self.session_activity:
                    del self.session_activity[sid]
                
                # 방에서도 제거
                await self.leave_room(sid, user_id)
                
                logger.info(f"Session unregistered: user_id={user_id}, sid={sid}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to unregister session: {str(e)}")
                return False
    
    async def join_room(self, sid: str, user_id: str, room_id: str) -> bool:
        """방 입장 - 여러 방 접속 방지"""
        async with self._lock:
            try:
                # 사용자가 이미 다른 방에 있는지 확인
                if user_id in self.user_rooms:
                    old_room_id = self.user_rooms[user_id]
                    if old_room_id != room_id:
                        logger.warning(f"User {user_id} already in room {old_room_id}, leaving before joining {room_id}")
                        await self.leave_room(sid, user_id)
                
                # 새 방 입장
                self.user_rooms[user_id] = room_id
                
                # 방 사용자 목록에 추가
                if room_id not in self.room_users:
                    self.room_users[room_id] = set()
                self.room_users[room_id].add(user_id)
                
                logger.info(f"User {user_id} joined room {room_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to join room: {str(e)}")
                return False
    
    async def leave_room(self, sid: str, user_id: str) -> bool:
        """방 나가기"""
        async with self._lock:
            try:
                if user_id not in self.user_rooms:
                    return True  # 이미 방에 없음
                
                room_id = self.user_rooms[user_id]
                del self.user_rooms[user_id]
                
                # 방 사용자 목록에서 제거
                if room_id in self.room_users:
                    self.room_users[room_id].discard(user_id)
                    if not self.room_users[room_id]:
                        del self.room_users[room_id]
                
                logger.info(f"User {user_id} left room {room_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to leave room: {str(e)}")
                return False
    
    async def get_user_session(self, user_id: str) -> Optional[str]:
        """사용자의 현재 세션 ID 조회"""
        async with self._lock:
            return self.user_sessions.get(user_id)
    
    async def get_session_user(self, sid: str) -> Optional[str]:
        """세션의 사용자 ID 조회"""
        async with self._lock:
            return self.session_users.get(sid)
    
    async def get_user_room(self, user_id: str) -> Optional[str]:
        """사용자의 현재 방 ID 조회"""
        async with self._lock:
            return self.user_rooms.get(user_id)
    
    async def get_room_users(self, room_id: str) -> Set[str]:
        """방에 있는 사용자 목록 조회"""
        async with self._lock:
            return self.room_users.get(room_id, set()).copy()
    
    async def is_user_in_room(self, user_id: str, room_id: str) -> bool:
        """사용자가 특정 방에 있는지 확인"""
        async with self._lock:
            return self.user_rooms.get(user_id) == room_id
    
    async def update_session_activity(self, sid: str):
        """세션 활동 시간 업데이트"""
        async with self._lock:
            self.session_activity[sid] = datetime.utcnow()
    
    async def _force_disconnect_session(self, sid: str, reason: str):
        """세션 강제 해제 (내부 메서드)"""
        try:
            # Socket.IO 서버에서 연결 해제
            from src.core.socket.server import sio
            await sio.disconnect(sid)
            
            # 에러 메시지 전송
            await sio.emit('force_disconnect', {
                'message': reason,
                'timestamp': datetime.utcnow().isoformat()
            }, room=sid)
            
            logger.info(f"Force disconnected session {sid}: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to force disconnect session {sid}: {str(e)}")
    
    async def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """비활성 세션 정리"""
        async with self._lock:
            try:
                current_time = datetime.utcnow()
                inactive_sessions = []
                
                for sid, last_activity in self.session_activity.items():
                    time_diff = (current_time - last_activity).total_seconds() / 60
                    if time_diff > timeout_minutes:
                        inactive_sessions.append(sid)
                
                for sid in inactive_sessions:
                    await self.unregister_session(sid)
                    logger.info(f"Cleaned up inactive session: {sid}")
                
                if inactive_sessions:
                    logger.info(f"Cleaned up {len(inactive_sessions)} inactive sessions")
                    
            except Exception as e:
                logger.error(f"Failed to cleanup inactive sessions: {str(e)}")
    
    def get_session_stats(self) -> Dict:
        """세션 통계 정보"""
        return {
            'total_sessions': len(self.session_users),
            'total_users': len(self.user_sessions),
            'total_rooms': len(self.room_users),
            'users_in_rooms': len(self.user_rooms)
        }

# 전역 세션 매니저 인스턴스
session_manager = SessionManager() 
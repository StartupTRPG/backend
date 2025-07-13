import logging
from typing import Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionManager:
    """세션 관리자 - 프로필별 방 참가 상태 관리"""
    
    def __init__(self):
        self.profile_rooms: Dict[str, str] = {}  # profile_id -> room_id
        self.room_profiles: Dict[str, Set[str]] = {}  # room_id -> set of profile_ids
        self.session_activity: Dict[str, datetime] = {}  # sid -> last_activity
    
    async def join_room(self, sid: str, profile_id: str, room_id: str) -> bool:
        """프로필을 방에 참가시킴"""
        try:
            # 기존 방에서 나가기
            if profile_id in self.profile_rooms:
                old_room_id = self.profile_rooms[profile_id]
                if old_room_id in self.room_profiles:
                    self.room_profiles[old_room_id].discard(profile_id)
                    if not self.room_profiles[old_room_id]:
                        del self.room_profiles[old_room_id]
            
            # 새 방에 참가
            self.profile_rooms[profile_id] = room_id
            if room_id not in self.room_profiles:
                self.room_profiles[room_id] = set()
            self.room_profiles[room_id].add(profile_id)
            
            # 세션 활동 시간 업데이트
            self.session_activity[sid] = datetime.utcnow()
            
            logger.info(f"Profile {profile_id} joined room {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining room: {e}")
            return False
    
    async def leave_room(self, sid: str, profile_id: str) -> bool:
        """프로필을 방에서 나가게 함"""
        try:
            if profile_id in self.profile_rooms:
                room_id = self.profile_rooms[profile_id]
                del self.profile_rooms[profile_id]
                
                if room_id in self.room_profiles:
                    self.room_profiles[room_id].discard(profile_id)
                    if not self.room_profiles[room_id]:
                        del self.room_profiles[room_id]
                
                # 세션 활동 시간 업데이트
                self.session_activity[sid] = datetime.utcnow()
                
                logger.info(f"Profile {profile_id} left room {room_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error leaving room: {e}")
            return False
    
    async def update_session_activity(self, sid: str) -> None:
        """세션 활동 시간 업데이트"""
        self.session_activity[sid] = datetime.utcnow()
    
    def get_profile_room(self, profile_id: str) -> Optional[str]:
        """프로필이 참가한 방 ID 반환"""
        return self.profile_rooms.get(profile_id)
    
    def get_room_profiles(self, room_id: str) -> Set[str]:
        """방에 참가한 프로필 ID 목록 반환"""
        return self.room_profiles.get(room_id, set())
    
    def cleanup_inactive_sessions(self, max_inactive_minutes: int = 30) -> None:
        """비활성 세션 정리"""
        now = datetime.utcnow()
        inactive_sids = []
        
        for sid, last_activity in self.session_activity.items():
            if (now - last_activity).total_seconds() > max_inactive_minutes * 60:
                inactive_sids.append(sid)
        
        for sid in inactive_sids:
            del self.session_activity[sid]

# 전역 인스턴스
session_manager = SessionManager() 
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging

from src.core.jwt_utils import get_current_admin
from src.modules.user.models import User
from src.modules.user.service import user_service
from src.core.session_manager import session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/session-stats")
async def get_session_stats(current_user: User = Depends(get_current_admin)) -> Dict:
    """세션 통계 조회 (관리자용)"""
    try:
        stats = session_manager.get_session_stats()
        return {
            "success": True,
            "data": stats,
            "message": "세션 통계를 조회했습니다."
        }
    except Exception as e:
        logger.error(f"Failed to get session stats: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 통계 조회 중 오류가 발생했습니다.")

@router.post("/cleanup-sessions")
async def cleanup_inactive_sessions(current_user: User = Depends(get_current_admin)) -> Dict:
    """비활성 세션 정리 (관리자용)"""
    try:
        await session_manager.cleanup_inactive_sessions()
        return {
            "success": True,
            "message": "비활성 세션이 정리되었습니다."
        }
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 정리 중 오류가 발생했습니다.")

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str, 
    role: str, 
    is_admin: bool = False,
    current_user: User = Depends(get_current_admin)
) -> Dict:
    """사용자 역할 업데이트 (관리자용)"""
    try:
        success = await user_service.update_user_role(user_id, role, is_admin)
        if not success:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "message": f"사용자 역할이 업데이트되었습니다. (role: {role}, is_admin: {is_admin})"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user role: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 역할 업데이트 중 오류가 발생했습니다.") 
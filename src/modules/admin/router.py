from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging

from src.core.jwt_utils import get_current_admin
from src.modules.user.models import User
from src.modules.user.service import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

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
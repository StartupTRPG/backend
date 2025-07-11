from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from src.core.jwt_utils import get_current_user
from src.modules.user.models import UserResponse
from .service import chat_service
from .models import RoomChatHistory

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/room/{room_id}/history", response_model=RoomChatHistory)
async def get_room_chat_history(
    room_id: str,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(50, ge=1, le=100, description="페이지당 메시지 수"),
    current_user: UserResponse = Depends(get_current_user)
):
    """방의 채팅 기록 조회"""
    try:
        # TODO: 사용자가 해당 방에 접근 권한이 있는지 확인
        # 현재는 로그인한 사용자라면 모든 방의 채팅 기록 조회 가능
        
        chat_history = await chat_service.get_room_messages(room_id, page, limit)
        return chat_history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 기록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/room/{room_id}/history")
async def delete_room_chat_history(
    room_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """방의 채팅 기록 삭제 (관리자 전용)"""
    try:
        # TODO: 관리자 권한 확인 또는 방 호스트 권한 확인
        
        deleted_count = await chat_service.delete_room_messages(room_id)
        return {
            "message": f"방 {room_id}의 채팅 기록이 삭제되었습니다.",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 기록 삭제 중 오류가 발생했습니다: {str(e)}") 
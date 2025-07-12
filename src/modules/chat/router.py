from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from src.core.jwt_utils import get_current_user
from src.modules.user.dto import UserResponse
from .service import chat_service
from .dto import RoomChatHistoryResponse, GetChatHistoryResponse, DeleteChatHistoryResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/room/{room_id}/history", response_model=GetChatHistoryResponse)
async def get_room_chat_history(
    room_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Messages per page"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get room chat history"""
    try:
        # TODO: Check if user has access to the room
        # Currently, any logged-in user can view chat history of all rooms
        
        chat_history = await chat_service.get_room_messages(room_id, page, limit)
        return GetChatHistoryResponse(
            data=chat_history,
            message="Chat history retrieved successfully.",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving chat history: {str(e)}")

@router.delete("/room/{room_id}/history", response_model=DeleteChatHistoryResponse)
async def delete_room_chat_history(
    room_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """방의 채팅 기록 삭제 (관리자 전용)"""
    try:
        # TODO: 관리자 권한 확인 또는 방 호스트 권한 확인
        
        deleted_count = await chat_service.delete_room_messages(room_id)
        return DeleteChatHistoryResponse(
            data={
                "deleted_count": deleted_count
            },
            message=f"방 {room_id}의 채팅 기록이 삭제되었습니다.",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"채팅 기록 삭제 중 오류가 발생했습니다: {str(e)}") 
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from src.core.jwt_utils import get_current_user
from src.core.response import ApiResponse
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
    """Get room chat history (all messages)"""
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
    """Delete all chat messages in a room"""
    try:
        deleted_count = await chat_service.delete_room_messages(room_id)
        return DeleteChatHistoryResponse(
            data={"deleted_count": deleted_count},
            message=f"Successfully deleted {deleted_count} messages from room {room_id}.",
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting chat history: {str(e)}") 
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from src.modules.user.dto import UserResponse
from src.modules.user.service import user_service
from src.core.jwt_utils import jwt_manager
from .service import room_service

from .dto import (
    RoomCreateRequest, RoomUpdateRequest, RoomResponse, 
    RoomListResponse
)
from .models import RoomStatus, RoomVisibility

router = APIRouter(prefix="/rooms", tags=["방"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """현재 사용자 정보를 가져오는 의존성"""
    try:
        payload = jwt_manager.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="유효하지 않은 액세스 토큰입니다.")
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="잘못된 토큰 타입입니다.")
        
        user = await user_service.get_user_by_id(payload["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다.")

@router.post("", response_model=RoomResponse)
async def create_room(
    room_data: RoomCreateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """방 생성"""
    try:
        room = await room_service.create_room(room_data, current_user)
        return room
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("", response_model=List[RoomListResponse])
async def list_rooms(
    status: Optional[RoomStatus] = Query(None, description="방 상태 필터"),
    visibility: Optional[RoomVisibility] = Query(None, description="방 공개 설정 필터"),
    search: Optional[str] = Query(None, description="검색어 (제목, 설명)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수")
):
    """방 목록 조회"""
    try:
        rooms = await room_service.list_rooms(
            status=status,
            visibility=visibility,
            search=search,
            page=page,
            limit=limit
        )
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/my", response_model=List[RoomListResponse])
async def get_my_rooms(
    current_user: UserResponse = Depends(get_current_user)
):
    """내가 참가한 방 목록 조회"""
    try:
        rooms = await room_service.get_user_rooms(current_user.id)
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내 방 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str):
    """방 정보 조회"""
    try:
        room = await room_service.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")
        return room
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 정보 조회 중 오류가 발생했습니다: {str(e)}")

# 방 참가/나가기는 Socket.IO에서 처리
# POST /rooms/{room_id}/join -> socket.emit('join_room')
# POST /rooms/{room_id}/leave -> socket.emit('leave_room')

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    room_data: RoomUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """방 설정 변경 (호스트만)"""
    try:
        room = await room_service.update_room(room_id, room_data, current_user.id)
        if not room:
            raise HTTPException(status_code=404, detail="방을 찾을 수 없습니다.")
        return room
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 설정 변경 중 오류가 발생했습니다: {str(e)}")

@router.post("/{room_id}/start")
async def start_game(
    room_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """게임 시작 (호스트만)"""
    try:
        success = await room_service.start_game(room_id, current_user.id)
        if success:
            return {"message": "게임이 시작되었습니다."}
        else:
            raise HTTPException(status_code=400, detail="게임 시작에 실패했습니다.")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"게임 시작 중 오류가 발생했습니다: {str(e)}")

@router.post("/{room_id}/end")
async def end_game(
    room_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """게임 종료 (호스트만)"""
    try:
        success = await room_service.end_game(room_id, current_user.id)
        if success:
            return {"message": "게임이 종료되었습니다."}
        else:
            raise HTTPException(status_code=400, detail="게임 종료에 실패했습니다.")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"게임 종료 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{room_id}")
async def delete_room(
    room_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """방 삭제 (호스트만)"""
    try:
        # 방장인지 확인하고 모든 플레이어를 내보낸 후 방 삭제
        success = await room_service.leave_room(room_id, current_user.id)
        if success:
            return {"message": "방이 삭제되었습니다."}
        else:
            raise HTTPException(status_code=400, detail="방 삭제에 실패했습니다.")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"방 삭제 중 오류가 발생했습니다: {str(e)}")

 
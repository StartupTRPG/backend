from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from src.core.response import ApiResponse
from src.modules.game.service import GameService
from src.modules.game.dto.game_requests import CreateGameRequest
from src.modules.user.service import user_service
from src.core.jwt_utils import jwt_manager

router = APIRouter(prefix="/game", tags=["game"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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

@router.post("/create")
async def create_game(
    request: CreateGameRequest,
    current_user = Depends(get_current_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    게임 생성 API
    """
    try:
        game_service = GameService()
        result = await game_service.create_game(request.room_id, request.players)
        return ApiResponse(data=result, message="게임이 성공적으로 생성되었습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/finish")
async def finish_game(
    request: Dict[str, str],
    current_user = Depends(get_current_user)
) -> ApiResponse[Dict[str, Any]]:
    """
    게임 종료 API
    """
    try:
        room_id = request.get("room_id")
        if not room_id:
            raise HTTPException(status_code=400, detail="room_id is required")
        
        game_service = GameService()
        result = await game_service.finish_game(room_id)
        return ApiResponse(data=result, message="게임이 성공적으로 종료되었습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
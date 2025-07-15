import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.core.socket.models import RoomMessage, SocketEventType
from src.modules.room.service import room_service
from src.modules.room.enums import PlayerRole

logger = logging.getLogger(__name__)

class RoomSocketService:
    """방 관련 Socket 이벤트 처리 서비스"""
    
    @staticmethod
    async def handle_join_room(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 입장 처리"""
        try:
            room_id = data.get('room_id')
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            # 방 존재 확인
            room = await room_service.get_room(room_id)
            if not room:
                logger.warning(f"Room {room_id} not found for user {user_id}")
                await sio.emit('error', {'message': 'Room not found or has been deleted.'}, room=sid)
                return None
            
            # 방 최대 인원 확인 (새로운 Room 모델 구조 사용)
            if room.current_players >= room.max_players:
                await sio.emit('error', {'message': 'Room is full.'}, room=sid)
                return None
            
            # user_id로 프로필 정보 조회
            user_id = session['user_id']
            username = session['username']
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None
            
            profile_id = profile.id
            
            # 게임 진행 중인지 확인 (기존 사용자는 재입장 가능)
            if room.status == 'playing':
                # 기존 플레이어인지 확인
                existing_player = room.get_player_by_profile_id(profile_id)
                if not existing_player:
                    await sio.emit('error', {'message': 'Cannot join room while game is in progress.'}, room=sid)
                    return None
                else:
                    logger.info(f"Existing player {profile.display_name} rejoining room {room_id} during game")
            
            # 이미 같은 방에 있는지 확인
            current_room = session.get('current_room')
            if current_room == room_id:
                logger.info(f"User {user_id} already in room {room_id}, ignoring duplicate join")
                return RoomMessage(
                    event_type=SocketEventType.JOIN_ROOM,
                    room_id=room_id,
                    profile_id=profile_id,
                    username=username
                )
            
            # 세션 매니저를 통한 방 입장 (여러 방 접속 방지)
            from src.core.session_manager import session_manager
            room_joined = await session_manager.join_room(sid, profile_id, room_id)
            if not room_joined:
                await sio.emit('error', {'message': 'Failed to join room.'}, room=sid)
                return None
            
            # 이미 다른 방에 있다면 나가기 (기존 로직 유지)
            current_room = session.get('current_room')
            if current_room and current_room != room_id:
                await RoomSocketService.handle_leave_room_internal(sio, sid, current_room)
            
            # 데이터베이스에 플레이어 추가 (이미 있는 경우 무시)
            success = await room_service.add_player_to_room_by_profile_id(room_id, profile_id)
            if not success:
                # 이미 방에 있는 경우는 성공으로 처리
                logger.info(f"Player {profile_id} already in room {room_id}, continuing with join process")
                # 성공으로 처리하고 계속 진행
            
            # Socket.IO 방에 입장
            await sio.enter_room(sid, room_id)
            await sio.emit('join_room', {
                'room_id': room_id,
                'profile_id': profile_id,
                'username': username,
                'display_name': profile.display_name,
                'message': f'{profile.display_name} has joined.',
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from src.core.socket.handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='join_room', room=room_id, profile=profile.display_name)
            
            # 세션 완전 재설정 (방 입장 시)
            new_session = {
                'user_id': session['user_id'],
                'username': session['username'],
                'access_token': session.get('access_token'),
                'current_room': room_id,
                'connected_at': session.get('connected_at', datetime.utcnow().isoformat()),
                'room_joined_at': datetime.utcnow().isoformat()
            }
            await sio.save_session(sid, new_session)
            
            # 방 사용자 목록 업데이트 (기존 로직 유지)
            from src.core.socket.server import room_profiles, connected_profiles
            if room_id not in room_profiles:
                room_profiles[room_id] = []
            room_profiles[room_id].append(sid)
            
            # 연결된 프로필 정보 업데이트
            if sid in connected_profiles:
                connected_profiles[sid]['current_room'] = room_id
            
            # 기존 토큰에 방 정보 추가
            from src.core.jwt_utils import jwt_manager
            current_token = session.get('access_token')
            updated_token = None
            
            if current_token:
                updated_token = jwt_manager.update_token_with_room_info(
                    token=current_token,
                    room_id=room_id,
                    room_permissions="write"
                )
                
                # 세션에 업데이트된 토큰 저장
                session['access_token'] = updated_token
                await sio.save_session(sid, session)
            
            logger.info(f"Profile {profile.display_name} joined room {room_id}")
            
            return RoomMessage(
                event_type=SocketEventType.JOIN_ROOM,
                room_id=room_id,
                profile_id=profile_id,
                username=session['username']
            )
            
        except Exception as e:
            logger.error(f"Join room error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while joining the room.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_leave_room(sio, sid: str, session: Dict[str, Any], data: Dict[str, Any]) -> Optional[RoomMessage]:
        """방 나가기 처리"""
        try:
            room_id = data.get('room_id') or session.get('current_room')
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            await RoomSocketService.handle_leave_room_internal(sio, sid, room_id)
            
            # user_id로 프로필 정보 조회
            user_id = session['user_id']
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            profile_id = profile.id if profile else None
            
            return RoomMessage(
                event_type=SocketEventType.LEAVE_ROOM,
                room_id=room_id,
                profile_id=profile_id,
                username=session['username']
            )
            
        except Exception as e:
            logger.error(f"Leave room error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while leaving the room.'}, room=sid)
            return None
    
    @staticmethod
    async def handle_start_game(sio, sid: str, session: dict, data: dict) -> Optional[RoomMessage]:
        """
        게임 시작 처리
        data: { "room_id": str }
        """
        try:
            room_id = data.get("room_id")
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
                
            user_id = session["user_id"]

            # 프로필 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                await sio.emit('error', {'message': 'Profile not found.'}, room=sid)
                return None

            # 게임 시작
            success = await room_service.start_game_by_profile_id(room_id, profile.id)
            if not success:
                await sio.emit('error', {'message': '게임 시작에 실패했습니다.'}, room=sid)
                return None

            # 방 정보 조회하여 플레이어 리스트 가져오기
            room = await room_service.room_repository.find_by_id(room_id)
            if not room:
                await sio.emit('error', {'message': '방 정보를 찾을 수 없습니다.'}, room=sid)
                return None

            # 플레이어 리스트 구성 (프로필 정보 조회)
            player_list = []
            for player in room.players:
                # 프로필 정보 조회
                player_profile = await user_profile_service.get_profile_by_id(player.profile_id)
                if player_profile:
                    player_info = {
                        "id": player.profile_id,
                        "name": player_profile.display_name,
                        "role": player.role.value if hasattr(player.role, 'value') else str(player.role)
                    }
                    player_list.append(player_info)
                else:
                    logger.warning(f"프로필을 찾을 수 없음: {player.profile_id}")
                    # 프로필이 없어도 기본 정보로 추가
                    player_info = {
                        "id": player.profile_id,
                        "name": f"Player_{player.profile_id[-8:]}",
                        "role": player.role.value if hasattr(player.role, 'value') else str(player.role)
                    }
                    player_list.append(player_info)

            # 모든 유저에게 즉시 게임 시작 브로드캐스트
            await sio.emit('start_game', {
                "room_id": room_id,
                "host_profile_id": profile.id,
                "host_display_name": profile.display_name,
                "message": f"{profile.display_name}님이 게임을 시작했습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }, room=room_id)
            
            # LLM 게임 생성을 비동기로 처리 (백그라운드에서 실행)
            async def create_llm_game():
                try:
                    from src.modules.game.service import game_service
                    game_result = await game_service.start_game(room_id, player_list)
                    
                    # 방의 모든 사용자에게 게임 생성 완료 알림
                    await sio.emit('game_created', {
                        'room_id': room_id,
                        'story': game_result.story,
                        'phase': 'context_creation'
                    }, room=room_id)
                    
                    logger.info(f"LLM 게임 생성 완료: {room_id}")
                    
                except Exception as e:
                    logger.error(f"LLM 게임 생성 실패: {room_id}, 오류: {str(e)}")
                    # LLM 게임 생성 실패해도 방 게임은 시작된 상태로 유지
                    await sio.emit('error', {'message': f'게임 스토리 생성에 실패했습니다: {str(e)}'}, room=room_id)
            
            # 비동기로 LLM 게임 생성 시작
            import asyncio
            asyncio.create_task(create_llm_game())
            
            # 브로드캐스트 로깅 추가
            from src.core.socket.handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='start_game', room=room_id, profile=profile.display_name)
            
            return RoomMessage(
                event_type=SocketEventType.START_GAME,
                room_id=room_id,
                profile_id=profile.id,
                host_profile_id=profile.id,
                host_display_name=profile.display_name
            )
            
        except Exception as e:
            logger.error(f"게임 시작 실패: {str(e)}")
            await sio.emit('error', {'message': f'게임 시작 실패: {str(e)}'}, room=sid)
            return None

    @staticmethod
    async def handle_finish_game(sio, sid: str, session: dict, data: dict) -> Optional[RoomMessage]:
        """
        게임 종료 처리
        data: { "room_id": str }
        """
        try:
            room_id = data.get("room_id")
            if not room_id:
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
                
            user_id = session["user_id"]

            # 프로필 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                await sio.emit('error', {'message': 'Profile not found.'}, room=sid)
                return None

            # 게임 종료
            success = await room_service.end_game_by_profile_id(room_id, profile.id)
            if not success:
                await sio.emit('error', {'message': '게임 종료에 실패했습니다.'}, room=sid)
                return None

            # 모든 유저에게 브로드캐스트
            logger.info(f"Broadcasting finish_game event to room {room_id}")
            await sio.emit('finish_game', {
                "room_id": room_id,
                "host_profile_id": profile.id,
                "host_display_name": profile.display_name,
                "message": f"{profile.display_name}님이 게임을 종료했습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from src.core.socket.handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='finish_game', room=room_id, profile=profile.display_name)
            logger.info(f"finish_game event broadcasted successfully to room {room_id}")
            
            return RoomMessage(
                event_type=SocketEventType.FINISH_GAME,
                room_id=room_id,
                host_profile_id=profile.id,
                host_display_name=profile.display_name,
                username=session['username']
            )
            
        except ValueError as e:
            await sio.emit('error', {'message': str(e)}, room=sid)
            return None
        except Exception as e:
            await sio.emit('error', {'message': f'게임 종료 중 오류: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_ready(sio, sid: str, session: dict, data: dict) -> Optional[RoomMessage]:
        """
        플레이어 레디/언레디 처리
        data: { "room_id": str, "ready": bool }
        """
        try:
            # 세션 검증
            if not session:
                logger.error(f"No session found for {sid}")
                await sio.emit('error', {'message': 'Session not found. Please reconnect.'}, room=sid)
                return None
            
            user_id = session.get("user_id")
            if not user_id:
                logger.error(f"No user_id in session for {sid}")
                await sio.emit('error', {'message': 'User not authenticated. Please login again.'}, room=sid)
                return None
            
            # 데이터 검증
            room_id = data.get("room_id")
            if not room_id:
                logger.error(f"No room_id provided for {sid}")
                await sio.emit('error', {'message': 'Room ID is required.'}, room=sid)
                return None
            
            ready = data.get("ready", False)

            # 프로필 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                logger.error(f"Profile not found for user_id: {user_id}")
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None

            # 방 존재 여부 확인
            from src.modules.room.repository import get_room_repository
            room_repo = get_room_repository()
            room = await room_repo.find_by_id(room_id)
            if not room:
                logger.error(f"Room not found: {room_id}")
                await sio.emit('error', {'message': 'Room not found.'}, room=sid)
                return None

            # 레디 상태 변경
            success = await room_service.set_player_ready(room_id, profile.id, ready)
            if not success:
                logger.error(f"Failed to set ready status for profile {profile.id} in room {room_id}")
                await sio.emit('error', {'message': 'Ready 상태 변경 실패.'}, room=sid)
                return None

            # 방 전체 레디 상태 확인
            all_ready = await room_service.is_all_ready(room_id)

            # 모든 유저에게 브로드캐스트
            await sio.emit('ready', {
                "room_id": room_id,
                "profile_id": profile.id,
                "ready": ready,
                "all_ready": all_ready
            }, room=room_id)
            
            # 브로드캐스트 로깅 추가
            from src.core.socket.handler import log_socket_message
            log_socket_message('SUCCESS', '브로드캐스트', event='ready', room=room_id, profile=profile.display_name, ready=ready, all_ready=all_ready)
            
            return RoomMessage(
                event_type=SocketEventType.READY,
                room_id=room_id,
                profile_id=profile.id,
                username=session['username']
            )
        except Exception as e:
            await sio.emit('error', {'message': f'레디 처리 중 오류: {str(e)}'}, room=sid)
            return None
    
    @staticmethod
    async def handle_leave_room_internal(sio, sid: str, room_id: str):
        """내부 방 나가기 처리"""
        try:
            session = await sio.get_session(sid)
            if not session:
                return
            
            user_id = session['user_id']
            username = session['username']
            
            # Profile 정보 조회
            from src.modules.profile.service import user_profile_service
            profile = await user_profile_service.get_profile_by_user_id(user_id)
            if not profile:
                await sio.emit('error', {'message': 'Profile not found. Please create a profile first.'}, room=sid)
                return None
            
            profile_id = profile.id
            
            # 데이터베이스에서 플레이어 제거 (호스트인 경우 방 삭제)
            is_host = False
            # Room 모델을 직접 조회하여 get_player_by_profile_id 메서드 사용
            from src.modules.room.repository import get_room_repository
            room_repo = get_room_repository()
            room = await room_repo.find_by_id(room_id)
            
            logger.info(f"Checking if profile {profile.id} is host in room {room_id}")
            if room:
                player = room.get_player_by_profile_id(profile.id)
                logger.info(f"Found player: {player}")
                if player:
                    logger.info(f"Player role: {player.role}, Profile ID: {player.profile_id}")
                    if player.role == PlayerRole.HOST:
                        is_host = True
                        logger.info(f"Profile {profile.id} is HOST - will delete room {room_id}")
                else:
                    logger.warning(f"Player not found for profile {profile.id} in room {room_id}")
            else:
                logger.warning(f"Room {room_id} not found")
            
            success = await room_service.remove_player_from_room_by_profile_id(room_id, profile_id)
            logger.info(f"Remove player result: {success}")
            
            # 호스트가 나가는 경우 방 삭제 알림
            if is_host:
                await sio.emit('room_deleted', {
                    'room_id': room_id,
                    'message': f'Room has been deleted by host {profile.display_name}.',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
                
                # 브로드캐스트 로깅 추가
                from src.core.socket.handler import log_socket_message
                log_socket_message('WARNING', '브로드캐스트', event='room_deleted', room=room_id, profile=profile.display_name)
            else:
                # 일반 사용자 나가기
                await sio.emit('leave_room', {
                    'room_id': room_id,
                    'profile_id': profile_id,
                    'username': username,
                    'display_name': profile.display_name,
                    'message': f'{profile.display_name} has left.',
                    'timestamp': datetime.utcnow().isoformat()
                }, room=room_id)
                
                # 브로드캐스트 로깅 추가
                from src.core.socket.handler import log_socket_message
                log_socket_message('SUCCESS', '브로드캐스트', event='leave_room', room=room_id, profile=profile.display_name)
            
            # Socket.IO 방에서 나가기
            await sio.leave_room(sid, room_id)
            
            # 세션 완전 정리 (방 나가기 시)
            cleaned_session = {
                'user_id': session['user_id'],
                'username': session['username'],
                'access_token': session.get('access_token'),
                'current_room': None,
                'connected_at': session.get('connected_at', datetime.utcnow().isoformat())
            }
            
            # 토큰에서 방 정보 제거
            from src.core.jwt_utils import jwt_manager
            current_token = session.get('access_token')
            if current_token:
                updated_token = jwt_manager.remove_room_info_from_token(current_token)
                cleaned_session['access_token'] = updated_token
            
            await sio.save_session(sid, cleaned_session)
            
            # 세션 매니저에서 방 나가기
            from src.core.session_manager import session_manager
            await session_manager.leave_room(sid, profile_id)
            
            # 방 사용자 목록에서 제거 (기존 로직 유지)
            from src.core.socket.server import room_profiles, connected_profiles
            if room_id in room_profiles and sid in room_profiles[room_id]:
                room_profiles[room_id].remove(sid)
                if not room_profiles[room_id]:
                    del room_profiles[room_id]
            
            if sid in connected_profiles:
                connected_profiles[sid]['current_room'] = None
            
            logger.info(f"Profile {profile.display_name} left room {room_id}")
            
        except Exception as e:
            logger.error(f"Leave room internal error for {sid}: {str(e)}")
            await sio.emit('error', {'message': 'An error occurred while leaving the room.'}, room=sid)
    
 
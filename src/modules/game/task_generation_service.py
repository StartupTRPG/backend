import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.core.mongodb import get_collection
from src.modules.room.service import room_service
from src.modules.game.llm_client import llm_client

logger = logging.getLogger(__name__)

class TaskGenerationService:
    """태스크 생성 서비스"""
    
    def __init__(self):
        self.task_collection = get_collection("tasks")
    
    async def generate_tasks_for_room(self, room_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """방의 모든 플레이어를 위한 태스크 생성 - LLM 백엔드 사용"""
        # 방 정보 확인
        room = await room_service.get_room(room_id)
        if not room:
            raise Exception("방을 찾을 수 없습니다.")
        
        # 게임 상태 확인
        from src.modules.game.service import game_service
        game_state = game_service.get_game_state(room_id)
        if not game_state:
            raise Exception("게임 상태를 찾을 수 없습니다.")
        
        # LLM 서버가 기대하는 형식으로 player_context_list 변환
        formatted_player_context_list = []
        for player_context in game_state.player_context_list:
            formatted_player_context_list.append({
                "id": player_context.get("player_id", ""),
                "name": player_context.get("player_name", ""),
                "role": player_context.get("player_role", ""),
                "context": player_context.get("player_context", {})
            })
        
        # LLM 서버에 태스크 생성 요청
        response = await llm_client.create_task(
            company_context=game_state.company_context,
            player_context_list=formatted_player_context_list
        )
        
        # 응답에서 태스크 리스트 추출
        task_list = response.get("task_list", {})
        
        # 태스크 데이터 저장
        await self._save_task_data(room_id, task_list)
        
        logger.info(f"LLM 백엔드를 통한 태스크 생성 완료: {room_id}, 플레이어 수: {len(room.players)}")
        return task_list
            
    
    async def _get_agenda_votes(self, room_id: str) -> List[Dict]:
        """아젠다 투표 결과 가져오기"""
        try:
            from src.modules.game.agenda_vote_service import agenda_vote_service
            
            # 방의 모든 아젠다 조회
            agenda_collection = get_collection("agendas")
            agendas = await agenda_collection.find({"room_id": room_id}).to_list(None)
            
            agenda_results = []
            for agenda in agendas:
                agenda_id = agenda["_id"]
                
                # 해당 아젠다의 투표 결과 조회
                votes = await agenda_vote_service.get_agenda_votes(agenda_id)
                
                # 투표 결과 분석
                vote_counts = {}
                for vote in votes:
                    vote_option = vote.get("vote")
                    vote_counts[vote_option] = vote_counts.get(vote_option, 0) + 1
                
                # 가장 많이 투표된 옵션 찾기
                winning_option = None
                max_votes = 0
                for option, count in vote_counts.items():
                    if count > max_votes:
                        max_votes = count
                        winning_option = option
                
                # 아젠다 결과 정보 구성
                agenda_result = {
                    "agenda_id": agenda_id,
                    "agenda_name": agenda.get("agenda_name", ""),
                    "agenda_description": agenda.get("agenda_description", ""),
                    "winning_option_id": winning_option,
                    "winning_option_text": self._get_option_text(agenda, winning_option),
                    "vote_results": vote_counts,
                    "total_votes": len(votes),
                    "is_winning": True  # 가장 많이 투표된 옵션
                }
                
                agenda_results.append(agenda_result)
            
            return agenda_results
            
        except Exception as e:
            logger.error(f"아젠다 투표 결과 조회 실패: {room_id}, 오류: {str(e)}")
            return []
    
    def _get_option_text(self, agenda: Dict, option_id: str) -> str:
        """아젠다 옵션의 텍스트 가져오기"""
        if not option_id:
            return ""
        
        agenda_options = agenda.get("agenda_options", [])
        for option in agenda_options:
            if option.get("agenda_option_id") == option_id:
                return option.get("agenda_option_text", "")
        
        return ""
    
    async def _save_task_data(self, room_id: str, task_list: Dict[str, List[Dict[str, Any]]]) -> bool:
        """태스크 데이터를 데이터베이스에 저장"""
        try:
            task_data = {
                "room_id": room_id,
                "task_list": task_list,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # 기존 태스크 데이터가 있으면 업데이트, 없으면 새로 생성
            existing_task = await self.task_collection.find_one({"room_id": room_id})
            
            if existing_task:
                await self.task_collection.update_one(
                    {"_id": existing_task["_id"]},
                    {"$set": task_data}
                )
            else:
                await self.task_collection.insert_one(task_data)
            
            logger.info(f"태스크 데이터 저장 완료: {room_id}")
            return True
            
        except Exception as e:
            logger.error(f"태스크 데이터 저장 실패: {room_id}, 오류: {str(e)}")
            return False
    
    async def get_task_data(self, room_id: str) -> Optional[Dict[str, Any]]:
        """저장된 태스크 데이터 조회"""
        try:
            task_data = await self.task_collection.find_one({"room_id": room_id})
            return task_data
            
        except Exception as e:
            logger.error(f"태스크 데이터 조회 실패: {room_id}, 오류: {str(e)}")
            return None

# 전역 인스턴스
task_generation_service = TaskGenerationService() 
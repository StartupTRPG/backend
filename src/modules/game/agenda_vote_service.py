from typing import Dict, List, Optional
from datetime import datetime
from src.core.mongodb import get_database
from src.modules.game.models.game_state import GameState
from src.core.socket.models.agenda_message import AgendaVoteRequest, AgendaVoteResponse, AgendaVoteUpdate


class AgendaVoteService:
    """아젠다 투표 서비스"""
    
    def __init__(self):
        self.db = get_database()
        self.agenda_collection = self.db.agendas
        self.vote_collection = self.db.agenda_votes
    
    async def vote_on_agenda(self, request: AgendaVoteRequest, user_id: str) -> AgendaVoteResponse:
        """아젠다에 투표"""
        try:
            # 아젠다 존재 확인
            agenda = await self.agenda_collection.find_one({"_id": request.agenda_id})
            if not agenda:
                return AgendaVoteResponse(
                    success=False,
                    message="존재하지 않는 아젠다입니다.",
                    agenda_id=request.agenda_id,
                    vote=request.selected_option_id,
                    total_votes=0,
                    vote_results={}
                )
            
            # 이미 투표했는지 확인
            existing_vote = await self.vote_collection.find_one({
                "agenda_id": request.agenda_id,
                "user_id": user_id
            })
            
            if existing_vote:
                # 기존 투표 업데이트
                await self.vote_collection.update_one(
                    {"_id": existing_vote["_id"]},
                    {"$set": {"vote": request.selected_option_id, "updated_at": datetime.utcnow()}}
                )
            else:
                # 새 투표 생성
                await self.vote_collection.insert_one({
                    "agenda_id": request.agenda_id,
                    "user_id": user_id,
                    "vote": request.selected_option_id,
                    "room_id": request.room_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
            
            # 투표 결과 계산
            vote_results = await self._calculate_vote_results(request.agenda_id)
            
            return AgendaVoteResponse(
                success=True,
                message="투표가 성공적으로 처리되었습니다.",
                agenda_id=request.agenda_id,
                vote=request.selected_option_id,
                total_votes=vote_results["total_votes"],
                vote_results=vote_results["results"]
            )
            
        except Exception as e:
            return AgendaVoteResponse(
                success=False,
                message=f"투표 처리 중 오류가 발생했습니다: {str(e)}",
                agenda_id=request.agenda_id,
                vote=request.vote,
                total_votes=0,
                vote_results={}
            )
    
    async def get_vote_update(self, agenda_id: str, user_id: str) -> AgendaVoteUpdate:
        """투표 업데이트 메시지 생성"""
        vote_results = await self._calculate_vote_results(agenda_id)
        
        # 아젠다 정보 가져오기
        agenda = await self.agenda_collection.find_one({"_id": agenda_id})
        if not agenda:
            return None
        
        # 투표 완료 여부 확인 (모든 플레이어가 투표했는지)
        room_players = agenda.get("participants", [])
        total_participants = len(room_players)
        is_complete = vote_results["total_votes"] >= total_participants
        
        return AgendaVoteUpdate(
            agenda_id=agenda_id,
            voter_id=user_id,
            vote="",  # 다른 사용자에게는 투표 내용을 숨김
            total_votes=vote_results["total_votes"],
            vote_results=vote_results["results"],
            is_complete=is_complete
        )
    
    async def _calculate_vote_results(self, agenda_id: str) -> Dict:
        """투표 결과 계산"""
        votes = await self.vote_collection.find({"agenda_id": agenda_id}).to_list(None)
        
        results = {}
        total_votes = len(votes)
        
        for vote in votes:
            vote_type = vote["vote"]
            results[vote_type] = results.get(vote_type, 0) + 1
        
        return {
            "total_votes": total_votes,
            "results": results
        }
    
    async def get_agenda_votes(self, agenda_id: str) -> List[Dict]:
        """아젠다의 모든 투표 조회"""
        votes = await self.vote_collection.find({"agenda_id": agenda_id}).to_list(None)
        return votes

# 전역 인스턴스
agenda_vote_service = AgendaVoteService() 
import httpx
import logging
from typing import Dict, Any, Optional
from src.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM 서버와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.LLM_API_BASE_URL
        self.timeout = 30.0  # 30초 타임아웃
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """LLM 서버에 HTTP 요청을 보내는 공통 메서드"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"LLM API 요청: {endpoint}")
                response = await client.post(url, json=data)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"LLM API 응답 성공: {endpoint}")
                return result
                
        except httpx.TimeoutException:
            logger.error(f"LLM API 타임아웃: {endpoint}")
            raise Exception(f"LLM 서버 응답 시간 초과: {endpoint}")
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP 오류: {endpoint}, 상태 코드: {e.response.status_code}")
            raise Exception(f"LLM 서버 오류: {e.response.status_code}")
        except Exception as e:
            logger.error(f"LLM API 요청 실패: {endpoint}, 오류: {str(e)}")
            raise Exception(f"LLM 서버 통신 실패: {str(e)}")
    
    async def create_game(self, player_list: list) -> Dict[str, Any]:
        """게임 생성"""
        data = {"player_list": player_list}
        return await self._make_request("/game", data)
    
    async def create_context(self, max_turn: int, story: str, player_list: list) -> Dict[str, Any]:
        """컨텍스트 생성"""
        data = {
            "max_turn": max_turn,
            "story": story,
            "player_list": player_list
        }
        return await self._make_request("/context", data)
    
    async def create_agenda(self, company_context: Dict[str, str], player_context_list: list) -> Dict[str, Any]:
        """아젠다 생성"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list
        }
        return await self._make_request("/agenda", data)
    
    async def create_task(self, company_context: Dict[str, str], player_context_list: list) -> Dict[str, Any]:
        """태스크 생성"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list
        }
        return await self._make_request("/task", data)
    
    async def create_overtime(self, company_context: Dict[str, str], player_context_list: list) -> Dict[str, Any]:
        """오버타임 생성"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list
        }
        return await self._make_request("/overtime", data)
    
    async def update_context(self, company_context: Dict[str, str], player_context_list: list, 
                           agenda_list: list, task_list: Dict[str, list], overtime_task_list: Dict[str, list]) -> Dict[str, Any]:
        """컨텍스트 업데이트"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list,
            "agenda_list": agenda_list,
            "task_list": task_list,
            "overtime_task_list": overtime_task_list
        }
        return await self._make_request("/context-update", data)
    
    async def create_explanation(self, company_context: Dict[str, Any], player_context_list: list) -> Dict[str, Any]:
        """설명 생성"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list
        }
        return await self._make_request("/explanation", data)
    
    async def calculate_result(self, company_context: Dict[str, str], player_context_list: list) -> Dict[str, Any]:
        """결과 계산"""
        data = {
            "company_context": company_context,
            "player_context_list": player_context_list
        }
        return await self._make_request("/result/", data)

    async def start_game(self, player_list: list) -> Dict[str, Any]:
        """게임 시작 (스토리 생성) - create_game과 동일"""
        return await self.create_game(player_list)

# 전역 LLM 클라이언트 인스턴스
llm_client = LLMClient() 
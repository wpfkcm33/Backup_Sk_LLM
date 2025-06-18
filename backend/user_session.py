# user_session.py - main.py에 추가할 사용자 세션 관리 코드

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid

# 사용자 데이터 저장 경로
USER_DATA_PATH = Path("user_data")
USER_DATA_PATH.mkdir(exist_ok=True)

class UserSessionManager:
    """사용자별 세션 및 히스토리 관리"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_user(self, username: str) -> Dict:
        """사용자 정보 가져오기 또는 생성"""
        user_path = USER_DATA_PATH / username
        user_path.mkdir(exist_ok=True)
        
        # 사용자 메타데이터
        meta_file = user_path / "metadata.json"
        if meta_file.exists():
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "username": username,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "total_queries": 0,
                "total_charts": 0
            }
            self.save_metadata(username, metadata)
        
        # 최근 접속 시간 업데이트
        metadata["last_accessed"] = datetime.now().isoformat()
        self.save_metadata(username, metadata)
        
        return metadata
    
    def save_metadata(self, username: str, metadata: Dict):
        """사용자 메타데이터 저장"""
        meta_file = USER_DATA_PATH / username / "metadata.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def save_query_history(self, username: str, query_data: Dict):
        """LLM 쿼리 히스토리 저장"""
        history_path = USER_DATA_PATH / username / "queries"
        history_path.mkdir(exist_ok=True)
        
        # 타임스탬프 기반 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
        
        query_record = {
            "id": query_id,
            "timestamp": datetime.now().isoformat(),
            "tab_id": query_data.get("tab_id"),
            "question": query_data.get("question"),
            "response": query_data.get("response"),
            "chart_generated": query_data.get("chart_generated", False)
        }
        
        # 개별 쿼리 저장
        query_file = history_path / f"{query_id}.json"
        with open(query_file, 'w', encoding='utf-8') as f:
            json.dump(query_record, f, ensure_ascii=False, indent=2)
        
        # 전체 히스토리 업데이트
        self.update_history_index(username, query_record)
        
        return query_id
    
    def update_history_index(self, username: str, query_record: Dict):
        """히스토리 인덱스 업데이트"""
        index_file = USER_DATA_PATH / username / "history_index.json"
        
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        # 최신 항목을 앞에 추가
        history.insert(0, {
            "id": query_record["id"],
            "timestamp": query_record["timestamp"],
            "question": query_record["question"][:100],  # 요약
            "chart_generated": query_record["chart_generated"]
        })
        
        # 최근 100개만 유지
        history = history[:100]
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def save_chart_config(self, username: str, chart_data: Dict):
        """차트 설정 저장"""
        charts_path = USER_DATA_PATH / username / "charts"
        charts_path.mkdir(exist_ok=True)
        
        chart_id = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        chart_file = charts_path / f"{chart_id}.json"
        
        chart_record = {
            "id": chart_id,
            "timestamp": datetime.now().isoformat(),
            "tab_id": chart_data.get("tab_id"),
            "config": chart_data.get("config"),
            "raw_data": chart_data.get("raw_data"),
            "query_id": chart_data.get("query_id")  # 관련 쿼리 ID
        }
        
        with open(chart_file, 'w', encoding='utf-8') as f:
            json.dump(chart_record, f, ensure_ascii=False, indent=2)
        
        return chart_id
    
    def get_user_history(self, username: str, limit: int = 20) -> List[Dict]:
        """사용자 히스토리 조회"""
        index_file = USER_DATA_PATH / username / "history_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        return history[:limit]
    
    def get_user_charts(self, username: str) -> List[Dict]:
        """사용자의 저장된 차트 목록 조회"""
        charts_path = USER_DATA_PATH / username / "charts"
        
        if not charts_path.exists():
            return []
        
        charts = []
        for chart_file in sorted(charts_path.glob("*.json"), reverse=True):
            with open(chart_file, 'r', encoding='utf-8') as f:
                chart_data = json.load(f)
                charts.append({
                    "id": chart_data["id"],
                    "timestamp": chart_data["timestamp"],
                    "tab_id": chart_data["tab_id"]
                })
        
        return charts[:50]  # 최근 50개

# 전역 세션 매니저 인스턴스
session_manager = UserSessionManager()

# FastAPI 라우트 추가
from fastapi import Path as FastPath

@app.get("/api/users/{username}/info")
async def get_user_info(username: str = FastPath(..., description="사용자명")):
    """사용자 정보 조회"""
    user_info = session_manager.get_or_create_user(username)
    return {
        "success": True,
        "user": user_info
    }

@app.get("/api/users/{username}/history")
async def get_user_history(
    username: str = FastPath(..., description="사용자명"),
    limit: int = 20
):
    """사용자 쿼리 히스토리 조회"""
    history = session_manager.get_user_history(username, limit)
    return {
        "success": True,
        "history": history
    }

@app.get("/api/users/{username}/charts")
async def get_user_charts(username: str = FastPath(..., description="사용자명")):
    """사용자 저장 차트 목록 조회"""
    charts = session_manager.get_user_charts(username)
    return {
        "success": True,
        "charts": charts
    }

@app.post("/api/users/{username}/llm/query")
async def process_user_llm_query(
    username: str,
    query: LLMQuery
):
    """사용자별 LLM 쿼리 처리 (히스토리 저장 포함)"""
    # 기존 LLM 처리 로직
    response = await process_llm_query(query)
    
    # 히스토리 저장
    query_data = {
        "tab_id": query.tab_id,
        "question": query.question,
        "response": response,
        "chart_generated": response.get("chart_request") == 1
    }
    
    query_id = session_manager.save_query_history(username, query_data)
    
    # 응답에 query_id 추가
    response["query_id"] = query_id
    
    # 사용자 통계 업데이트
    user_info = session_manager.get_or_create_user(username)
    user_info["total_queries"] += 1
    if query_data["chart_generated"]:
        user_info["total_charts"] += 1
    session_manager.save_metadata(username, user_info)
    
    return response

@app.post("/api/users/{username}/charts/save")
async def save_user_chart(
    username: str,
    chart_data: Dict
):
    """사용자 차트 저장"""
    chart_id = session_manager.save_chart_config(username, chart_data)
    return {
        "success": True,
        "chart_id": chart_id
    }

@app.get("/api/users/{username}/charts/{chart_id}")
async def get_user_chart(
    username: str,
    chart_id: str
):
    """특정 차트 조회"""
    chart_file = USER_DATA_PATH / username / "charts" / f"{chart_id}.json"
    
    if not chart_file.exists():
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다")
    
    with open(chart_file, 'r', encoding='utf-8') as f:
        chart_data = json.load(f)
    
    return {
        "success": True,
        "chart": chart_data
    }
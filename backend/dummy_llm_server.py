# dummy_llm_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import random
import json
import re

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = 0.7

# SQL 쿼리 생성 함수
def generate_sql_query(question: str, tab_id: str) -> Dict[str, Any]:
    """질문에 기반하여 SQL 쿼리 생성"""
    question_lower = question.lower()
    
    # 테이블 이름
    table_name = f"{tab_id}"
    
    # 기본 응답
    response = {
        "chart_request": 0,
        "description": "요청하신 분석을 수행했습니다."
    }
    
    # 키워드 기반 SQL 생성
    if "2024" in question:
        if "레이팅" in question or "rating" in question_lower:
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT quarter, AVG(rating) as avg_rating FROM {table_name} WHERE year = 2024 GROUP BY quarter ORDER BY quarter",
                "chart_type": "bar",
                "description": "2024년 분기별 평균 레이팅을 분석했습니다."
            }
        elif "매출" in question or "sales" in question_lower:
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT quarter, SUM(sales) as total_sales FROM {table_name} WHERE year = 2024 GROUP BY quarter ORDER BY quarter",
                "chart_type": "line",
                "description": "2024년 분기별 총 매출을 분석했습니다."
            }
    
    elif "카테고리" in question or "category" in question_lower:
        if "매출" in question or "sales" in question_lower:
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT category, SUM(sales) as total_sales FROM {table_name} GROUP BY category ORDER BY total_sales DESC",
                "chart_type": "doughnut",
                "description": "카테고리별 총 매출을 분석했습니다."
            }
        elif "레이팅" in question or "rating" in question_lower:
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT category, AVG(rating) as avg_rating FROM {table_name} GROUP BY category ORDER BY avg_rating DESC",
                "chart_type": "bar",
                "description": "카테고리별 평균 레이팅을 분석했습니다."
            }
    
    elif "연도" in question or "year" in question_lower:
        response = {
            "chart_request": 1,
            "sql_query": f"SELECT year, AVG(rating) as avg_rating, SUM(sales) as total_sales FROM {table_name} GROUP BY year ORDER BY year",
            "chart_type": "line",
            "description": "연도별 추이를 분석했습니다."
        }
    
    elif "상위" in question or "top" in question_lower:
        if tab_id == "tab2":  # 제품 정보
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT product_name, stock FROM {table_name} ORDER BY stock DESC LIMIT 10",
                "chart_type": "bar",
                "description": "재고가 많은 상위 10개 제품을 표시했습니다."
            }
        elif tab_id == "tab3":  # 고객 분석
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT region, COUNT(*) as customer_count FROM {table_name} GROUP BY region ORDER BY customer_count DESC LIMIT 5",
                "chart_type": "pie",
                "description": "고객이 많은 상위 5개 지역을 표시했습니다."
            }
    
    elif "분기" in question or "quarter" in question_lower:
        response = {
            "chart_request": 1,
            "sql_query": f"SELECT quarter, AVG(rating) as avg_rating FROM {table_name} GROUP BY quarter ORDER BY quarter",
            "chart_type": "bar",
            "description": "분기별 평균 레이팅을 분석했습니다."
        }
    
    elif "지역" in question or "region" in question_lower:
        if tab_id == "tab3":
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT region, AVG(satisfaction_score) as avg_satisfaction FROM {table_name} GROUP BY region ORDER BY avg_satisfaction DESC",
                "chart_type": "bar",
                "description": "지역별 평균 만족도를 분석했습니다."
            }
    
    # 차트 요청이지만 구체적이지 않은 경우
    elif "차트" in question or "그래프" in question or "보여" in question:
        if tab_id == "tab1":
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT year, quarter, AVG(rating) as avg_rating FROM {table_name} GROUP BY year, quarter ORDER BY year, quarter",
                "chart_type": "line",
                "description": "연도 및 분기별 평균 레이팅 추이를 보여드립니다."
            }
        elif tab_id == "tab2":
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT category, COUNT(*) as product_count FROM {table_name} GROUP BY category",
                "chart_type": "pie",
                "description": "카테고리별 제품 분포를 보여드립니다."
            }
        elif tab_id == "tab3":
            response = {
                "chart_request": 1,
                "sql_query": f"SELECT region, COUNT(*) as customer_count FROM {table_name} GROUP BY region",
                "chart_type": "doughnut",
                "description": "지역별 고객 분포를 보여드립니다."
            }
    
    return response

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # 사용자 메시지 추출
        user_message = ""
        system_message = ""
        
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content
            elif msg.role == "system":
                system_message = msg.content
        
        # 시스템 메시지에서 탭 ID 추출
        tab_id = "tab1"  # 기본값
        if "tab1_data" in system_message:
            tab_id = "tab1"
        elif "tab2_data" in system_message:
            tab_id = "tab2"
        elif "tab3_data" in system_message:
            tab_id = "tab3"
        
        # SQL 쿼리 생성
        result = generate_sql_query(user_message, tab_id)
        
        # LLM API 형식으로 응답 구성
        return {
            "id": f"chatcmpl-{random.randint(1000000, 9999999)}",
            "object": "chat.completion",
            "created": 1234567890,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(result, ensure_ascii=False)
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 150,
                "total_tokens": 250
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "dummy-llm-api"}

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "test-model",
                "object": "model",
                "created": 1234567890,
                "owned_by": "test"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🤖 더미 LLM API 서버 시작 (포트: 8001)")
    print("📝 지원하는 질문 예시:")
    print("   - 2024년 레이팅을 보여줘")
    print("   - 카테고리별 매출 분석해줘")
    print("   - 상위 10개 제품의 재고 현황")
    print("   - 지역별 고객 분포를 차트로 보여줘")
    uvicorn.run(app, host="0.0.0.0", port=8001)
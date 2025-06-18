# main.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import oracledb
import sqlite3
import pandas as pd
import httpx
import json
import asyncio
import os
from datetime import datetime, timedelta
import uuid
from pathlib import Path
from fastapi import Path as FastPath

app = FastAPI()

# CORS 설정 (모든 origin 허용 - 개발용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Oracle 클라이언트 초기화 (옵션)
USE_THICK_MODE = False  # True로 변경하면 Instant Client 사용

if USE_THICK_MODE:
    client_lib_dir = r"/home/humandeep/oracle/instantclient_21_8"
    if os.path.exists(client_lib_dir):
        print(f"✅ Oracle 클라이언트 경로: {client_lib_dir}")
        try:
            if 'LD_LIBRARY_PATH' in os.environ:
                os.environ['LD_LIBRARY_PATH'] = f"{client_lib_dir}:{os.environ['LD_LIBRARY_PATH']}"
            else:
                os.environ['LD_LIBRARY_PATH'] = client_lib_dir
            
            oracledb.init_oracle_client(lib_dir=client_lib_dir)
            print("✅ Oracle 클라이언트 초기화 성공 (Thick 모드)")
        except Exception as e:
            print(f"⚠️ Oracle 클라이언트 초기화 경고: {e}")
            print("💡 해결 방법: sudo apt-get install libaio-dev")
            print("🔄 Thin 모드로 전환합니다...")
            USE_THICK_MODE = False
    else:
        print(f"❌ Oracle 클라이언트 경로가 없습니다: {client_lib_dir}")
        USE_THICK_MODE = False

if not USE_THICK_MODE:
    print("✅ Oracle Thin 모드 사용 (Instant Client 불필요)")

# Oracle DB 연결 설정
# 테스트용 로컬 Oracle 연결 정보
ORACLE_USER = "system"
ORACLE_PASSWORD = "Test123"
ORACLE_DSN = "localhost:1521/XE"

# 운영 서버 연결 정보 (주석 처리)
# ORACLE_USER = "hiq1"
# ORACLE_PASSWORD = "hiq11!"
# ORACLE_DSN = "10.158.122.119/HIQ1DEV"

# LLM API 설정
LLM_API_KEY = "test-api-key"  # 테스트용 더미 키
LLM_API_URL = "http://localhost:8001/v1/chat/completions"

# 운영 API 설정 (주석 처리)
# LLM_API_KEY = os.environ.get("API_KEY", "")
# LLM_API_URL = "http://dev.assistant.llm.skhynix.com/v1/chat/completions"

# 탭별 고정 SQL 쿼리
TAB_QUERIES = {
    "tab1": """
        SELECT year, quarter, category, rating, sales
        FROM performance_data
        WHERE year >= 2022
        ORDER BY year, quarter
    """,
    "tab2": """
        SELECT product_id, product_name, category, price, stock
        FROM products
        WHERE status = 'active'
    """,
    "tab3": """
        SELECT customer_id, region, total_orders, satisfaction_score
        FROM customer_metrics
        WHERE last_order_date >= ADD_MONTHS(SYSDATE, -12)
    """
}

# SQLite in-memory DB 관리
class MemoryDB:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
    def store_data(self, table_name: str, df: pd.DataFrame):
        """데이터프레임을 테이블로 저장"""
        df.to_sql(table_name, self.conn, if_exists='replace', index=False)
        print(f"✅ {table_name} 테이블 저장 완료: {len(df)}행")
    
    def execute_query(self, query: str, timeout: int = 10) -> pd.DataFrame:
        """SQL 쿼리 실행"""
        try:
            return pd.read_sql_query(query, self.conn)
        except Exception as e:
            print(f"❌ SQL 실행 오류: {e}")
            print(f"   쿼리: {query}")
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master WHERE type='table'", 
                self.conn
            )
            print(f"   현재 테이블: {tables['name'].tolist()}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone()[0] > 0
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """테이블 스키마 정보 조회"""
        if not self.table_exists(table_name):
            return []
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        self.conn.close()

# 전역 메모리 DB 인스턴스
memory_db = MemoryDB()

# Pydantic 모델
class LLMQuery(BaseModel):
    question: str
    tab_id: str

class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    tab_id: str
    grid_config: Dict[str, Any]

class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    grid_config: Optional[Dict[str, Any]] = None

# 테스트 모드 설정
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    print("🧪 테스트 모드 활성화 - Oracle 연결 없이 샘플 데이터 사용")

# Oracle DB 연결 함수
def get_oracle_connection():
    if TEST_MODE:
        class DummyConnection:
            def cursor(self):
                return None
            def close(self):
                pass
        return DummyConnection()
    
    try:
        print(f"🔌 Oracle DB 연결 시도: {ORACLE_DSN}")
        connection = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        print("✅ Oracle DB 연결 성공")
        return connection
    except oracledb.Error as e:
        error_obj, = e.args
        print(f"❌ Oracle DB 연결 실패:")
        print(f"   - 오류 코드: {error_obj.code}")
        print(f"   - 오류 메시지: {error_obj.message}")
        
        if error_obj.code == 12541:
            raise HTTPException(
                status_code=500, 
                detail="Oracle 데이터베이스가 실행 중이 아닙니다."
            )
        elif error_obj.code == 1017:
            raise HTTPException(
                status_code=500, 
                detail="Oracle 사용자명 또는 비밀번호가 올바르지 않습니다."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Oracle DB 연결 실패: {error_obj.message}"
            )
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터베이스 연결 실패: {str(e)}")

# 데이터를 Chart.js 형식으로 변환
def convert_to_chartjs_format(df: pd.DataFrame, chart_type: str = "bar") -> Dict[str, Any]:
    if df.empty:
        return None
    
    labels = df.iloc[:, 0].tolist()
    datasets = []
    
    colors = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c"]
    
    for i, col in enumerate(df.columns[1:]):
        if pd.api.types.is_numeric_dtype(df[col]):
            datasets.append({
                "label": col,
                "data": df[col].tolist(),
                "backgroundColor": colors[i % len(colors)],
                "borderColor": colors[i % len(colors)],
                "borderWidth": 1
            })
    
    return {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                },
                "tooltip": {
                    "enabled": True
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    }

# 메모리에서 샘플 데이터 생성
def generate_sample_data(tab_id):
    """Oracle 연결 실패 시 사용할 샘플 데이터 생성"""
    if tab_id == "tab1":
        data = []
        for year in [2022, 2023, 2024]:
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                for category in ['A', 'B', 'C']:
                    data.append({
                        'year': year,
                        'quarter': quarter,
                        'category': category,
                        'rating': round(3.5 + hash(f"{year}{quarter}{category}") % 15 / 10, 1),
                        'sales': 1000000 + hash(f"{year}{quarter}{category}") % 1000000
                    })
        return pd.DataFrame(data)
    
    elif tab_id == "tab2":
        products = []
        for i in range(10):
            products.append({
                'product_id': f'PRD{i+1:03d}',
                'product_name': f'제품 {i+1}',
                'category': ['전자제품', '액세서리', '저장장치'][i % 3],
                'price': 50000 + (i * 100000),
                'stock': 100 + (i * 50)
            })
        return pd.DataFrame(products)
    
    elif tab_id == "tab3":
        customers = []
        regions = ['서울', '부산', '대구', '인천', '광주', '대전']
        for i in range(20):
            customers.append({
                'customer_id': f'CUST{i+1:03d}',
                'region': regions[i % len(regions)],
                'total_orders': 20 + (i * 3),
                'satisfaction_score': round(3.5 + (i % 15) / 10, 1)
            })
        return pd.DataFrame(customers)
    
    return pd.DataFrame()

# 테이블 확인 및 생성 함수
def check_and_create_tables(conn):
    """테이블이 없으면 생성"""
    if TEST_MODE:
        return
        
    cursor = conn.cursor()
    
    tables = ['PERFORMANCE_DATA', 'PRODUCTS', 'CUSTOMER_METRICS']
    for table in tables:
        cursor.execute(f"""
            SELECT COUNT(*) FROM user_tables WHERE table_name = '{table}'
        """)
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            print(f"📝 {table} 테이블 생성 중...")
            # 테이블 생성 로직 (간략화)
            conn.commit()
            print(f"✅ {table} 테이블 생성 완료")

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
        
        query_file = history_path / f"{query_id}.json"
        with open(query_file, 'w', encoding='utf-8') as f:
            json.dump(query_record, f, ensure_ascii=False, indent=2)
        
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
        
        history.insert(0, {
            "id": query_record["id"],
            "timestamp": query_record["timestamp"],
            "question": query_record["question"][:100],
            "chart_generated": query_record["chart_generated"]
        })
        
        history = history[:100]  # 최근 100개만 유지
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_user_history(self, username: str, limit: int = 50) -> List[Dict]:
        """사용자 히스토리 조회"""
        index_file = USER_DATA_PATH / username / "history_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        return history[:limit]

class PresetManager:
    """프리셋 관리 클래스"""
    
    def __init__(self, username: str):
        self.username = username
        self.user_path = USER_DATA_PATH / username
        self.preset_path = self.user_path / "presets"
        self.preset_path.mkdir(exist_ok=True)
        self.queries_path = self.user_path / "queries"
    
    def save_preset(self, preset_data: Dict) -> str:
        """프리셋 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preset_id = f"preset_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        preset_record = {
            "id": preset_id,
            "name": preset_data["name"],
            "description": preset_data.get("description", ""),
            "tab_id": preset_data["tab_id"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "grid_config": preset_data["grid_config"]
        }
        
        # 개별 프리셋 파일 저장
        preset_file = self.preset_path / f"{preset_id}.json"
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(preset_record, f, ensure_ascii=False, indent=2)
        
        # 프리셋 인덱스 업데이트
        self.update_preset_index(preset_record)
        
        return preset_id
    
    def update_preset(self, preset_id: str, update_data: Dict) -> bool:
        """프리셋 업데이트"""
        preset_file = self.preset_path / f"{preset_id}.json"
        if not preset_file.exists():
            return False
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            preset_data = json.load(f)
        
        # 업데이트 적용
        if "name" in update_data:
            preset_data["name"] = update_data["name"]
        if "description" in update_data:
            preset_data["description"] = update_data["description"]
        if "grid_config" in update_data:
            preset_data["grid_config"] = update_data["grid_config"]
        
        preset_data["updated_at"] = datetime.now().isoformat()
        
        # 파일 저장
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, ensure_ascii=False, indent=2)
        
        # 인덱스 업데이트
        self.update_preset_index(preset_data)
        
        return True
    
    def delete_preset(self, preset_id: str) -> bool:
        """프리셋 삭제"""
        preset_file = self.preset_path / f"{preset_id}.json"
        if not preset_file.exists():
            return False
        
        # 파일 삭제
        preset_file.unlink()
        
        # 인덱스에서 제거
        self.remove_from_index(preset_id)
        
        return True
    
    def get_preset_list(self, tab_id: str = None) -> List[Dict]:
        """프리셋 목록 조회"""
        index_file = self.preset_path / "preset_index.json"
        
        if not index_file.exists():
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        presets = index_data.get("presets", [])
        
        # 탭별 필터링
        if tab_id:
            presets = [p for p in presets if p.get("tab_id") == tab_id]
        
        return presets
    
    def load_preset(self, preset_id: str) -> Dict:
        """프리셋 로드 (차트 데이터 포함)"""
        preset_file = self.preset_path / f"{preset_id}.json"
        if not preset_file.exists():
            raise HTTPException(404, "프리셋을 찾을 수 없습니다")
        
        with open(preset_file, 'r', encoding='utf-8') as f:
            preset_data = json.load(f)
        
        print(f"🔍 프리셋 로드: {preset_id}")
        print(f"🔍 프리셋 데이터: {preset_data}")
        
        # 차트 데이터 로드 및 병합
        resolved_charts = []
        for chart_config in preset_data["grid_config"]["charts"]:
            try:
                print(f"🔍 차트 설정: {chart_config}")
                
                if chart_config["source"]["type"] == "query_reference":
                    # 쿼리 참조 방식
                    query_id = chart_config["source"]["query_id"]
                    print(f"🔍 쿼리 참조: {query_id}")
                    
                    query_data = self.load_query_data(query_id)
                    print(f"🔍 쿼리 데이터 로드됨: {list(query_data.keys())}")
                    
                    resolved_chart = self.merge_chart_data(query_data, chart_config["source"])
                    print(f"🔍 병합된 차트: {list(resolved_chart.keys())}")
                else:
                    # 인라인 데이터 방식
                    resolved_chart = chart_config["source"]["chart_data"]
                    print(f"🔍 인라인 차트: {list(resolved_chart.keys()) if resolved_chart else 'None'}")
                
                # ID가 없는 경우 생성
                if "id" not in resolved_chart or not resolved_chart["id"]:
                    resolved_chart["id"] = f"preset_chart_{uuid.uuid4().hex[:8]}"
                
                resolved_charts.append({
                    "position": chart_config["position"],
                    "chart_data": resolved_chart
                })
                print(f"✅ 차트 처리 완료 (position {chart_config['position']})")
                
            except Exception as e:
                print(f"⚠️ 차트 로드 실패 (position {chart_config['position']}): {e}")
                import traceback
                traceback.print_exc()
                # 오류가 있는 차트는 건너뛰기
                continue
        
        print(f"🔍 최종 resolved_charts: {len(resolved_charts)}개")
        for i, chart in enumerate(resolved_charts):
            chart_data = chart["chart_data"]
            print(f"  - 차트 {i}: keys={list(chart_data.keys())}")
            if "config" in chart_data:
                print(f"    config: {list(chart_data['config'].keys())}")
        
        return {
            "preset": preset_data,
            "charts": resolved_charts
        }
    
    def load_query_data(self, query_id: str) -> Dict:
        """쿼리 파일에서 데이터 로드"""
        query_file = self.queries_path / f"{query_id}.json"
        if not query_file.exists():
            raise Exception(f"쿼리 파일을 찾을 수 없습니다: {query_id}")
        
        with open(query_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def merge_chart_data(self, query_data: Dict, source_config: Dict) -> Dict:
        """쿼리 데이터와 프리셋 설정 병합"""
        print(f"🔍 merge_chart_data 호출")
        print(f"🔍 query_data keys: {list(query_data.keys())}")
        print(f"🔍 source_config: {source_config}")
        
        # 쿼리 데이터에서 response 부분 추출
        if "response" in query_data:
            chart_data = query_data["response"].copy()
        else:
            print("❌ query_data에 response 키가 없습니다")
            chart_data = query_data.copy()
        
        print(f"🔍 chart_data keys after copy: {list(chart_data.keys())}")
        
        # ChartComponent가 기대하는 구조로 변환
        # response에서 나온 데이터는 이미 올바른 형태여야 함
        if "chart_config" in chart_data:
            # config 키로 이동
            chart_data["config"] = chart_data["chart_config"]
            print(f"🔍 chart_config를 config로 복사")
        
        # ID가 없는 경우 생성
        if "id" not in chart_data:
            chart_data["id"] = f"query_chart_{uuid.uuid4().hex[:8]}"
            print(f"🔍 ID 생성: {chart_data['id']}")
        
        # 커스텀 제목 적용
        if "title" in source_config:
            chart_data["title"] = source_config["title"]
            if "config" in chart_data and "options" in chart_data["config"]:
                if "plugins" not in chart_data["config"]["options"]:
                    chart_data["config"]["options"]["plugins"] = {}
                if "title" not in chart_data["config"]["options"]["plugins"]:
                    chart_data["config"]["options"]["plugins"]["title"] = {}
                chart_data["config"]["options"]["plugins"]["title"]["text"] = source_config["title"]
            print(f"🔍 커스텀 제목 적용: {source_config['title']}")
        
        # 커스텀 옵션 적용 (추후 확장 가능)
        if "custom_options" in source_config:
            # 깊은 병합 로직 구현 (예: lodash merge와 유사)
            pass
        
        print(f"🔍 최종 chart_data keys: {list(chart_data.keys())}")
        if "config" in chart_data:
            print(f"🔍 config keys: {list(chart_data['config'].keys())}")
        
        return chart_data
    
    def update_preset_index(self, preset_data: Dict):
        """프리셋 인덱스 업데이트"""
        index_file = self.preset_path / "preset_index.json"
        
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {"presets": [], "last_updated": ""}
        
        # 프리셋 요약 정보
        preset_summary = {
            "id": preset_data["id"],
            "name": preset_data["name"],
            "description": preset_data["description"],
            "tab_id": preset_data["tab_id"],
            "chart_count": len(preset_data["grid_config"]["charts"]),
            "created_at": preset_data["created_at"],
            "updated_at": preset_data["updated_at"]
        }
        
        # 기존 프리셋 업데이트 또는 새로 추가
        existing_index = next((i for i, p in enumerate(index_data["presets"]) 
                              if p["id"] == preset_data["id"]), None)
        
        if existing_index is not None:
            index_data["presets"][existing_index] = preset_summary
        else:
            index_data["presets"].insert(0, preset_summary)
        
        index_data["last_updated"] = datetime.now().isoformat()
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def remove_from_index(self, preset_id: str):
        """인덱스에서 프리셋 제거"""
        index_file = self.preset_path / "preset_index.json"
        
        if not index_file.exists():
            return
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        index_data["presets"] = [p for p in index_data["presets"] if p["id"] != preset_id]
        index_data["last_updated"] = datetime.now().isoformat()
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

# 전역 세션 매니저 인스턴스
session_manager = UserSessionManager()

# ======================
# API 엔드포인트들
# ======================

# 헬스 체크
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 데이터베이스 연결 테스트
@app.get("/api/test/db-connection")
async def test_db_connection():
    """데이터베이스 연결 테스트"""
    try:
        if TEST_MODE:
            return {
                "status": "test_mode",
                "message": "테스트 모드에서 실행 중입니다.",
                "tables": {}
            }
            
        conn = get_oracle_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 'Connected' as status, SYSDATE as current_time FROM dual")
        result = cursor.fetchone()
        
        tables = {}
        for table_name in ['PERFORMANCE_DATA', 'PRODUCTS', 'CUSTOMER_METRICS']:
            cursor.execute(f"""
                SELECT COUNT(*) FROM user_tables WHERE table_name = '{table_name}'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                tables[table_name] = {"exists": True, "row_count": count}
            else:
                tables[table_name] = {"exists": False, "row_count": 0}
        
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "connection": {
                "status": result[0],
                "server_time": str(result[1]),
                "dsn": ORACLE_DSN,
                "user": ORACLE_USER
            },
            "tables": tables
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "dsn": ORACLE_DSN,
            "user": ORACLE_USER
        }

# 사용자 정보 조회
@app.get("/api/users/{username}/info")
async def get_user_info(username: str = FastPath(..., description="사용자명")):
    """사용자 정보 조회"""
    user_info = session_manager.get_or_create_user(username)
    return {
        "success": True,
        "user": user_info
    }

# 사용자 히스토리 조회
@app.get("/api/users/{username}/history")
async def get_user_history(
    username: str = FastPath(..., description="사용자명"),
    limit: int = 50
):
    """사용자 쿼리 히스토리 조회"""
    history = session_manager.get_user_history(username, limit)
    return {
        "success": True,
        "history": history
    }

# 히스토리 상세 조회
@app.get("/api/users/{username}/history/{query_id}")
async def get_user_history_detail(
    username: str = FastPath(..., description="사용자명"),
    query_id: str = FastPath(..., description="쿼리 ID")
):
    """특정 쿼리 히스토리 상세 조회"""
    query_file = USER_DATA_PATH / username / "queries" / f"{query_id}.json"
    
    if not query_file.exists():
        raise HTTPException(status_code=404, detail="쿼리를 찾을 수 없습니다")
    
    try:
        with open(query_file, 'r', encoding='utf-8') as f:
            query_data = json.load(f)
        
        return {
            "success": True,
            "query": query_data
        }
    except Exception as e:
        print(f"❌ 쿼리 로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"쿼리 로드 실패: {str(e)}")

# 탭 데이터 로드 (사용자 구분 없이 공통 사용)
@app.get("/api/users/{username}/api/tabs/{tab_id}/data")
async def get_tab_data(tab_id: str):
    """탭 데이터 로드 - 사용자 구분 없이 공통 사용"""
    if tab_id not in TAB_QUERIES:
        raise HTTPException(status_code=404, detail="탭을 찾을 수 없습니다")
    
    try:
        print(f"📊 {tab_id} 데이터 로드 시작...")
        
        if TEST_MODE:
            print("🧪 테스트 모드: 샘플 데이터 생성")
            df = generate_sample_data(tab_id)
        else:
            conn = get_oracle_connection()
            cursor = conn.cursor()
            try:
                check_and_create_tables(conn)
                df = pd.read_sql(TAB_QUERIES[tab_id], conn)
                print(f"✅ 데이터 로드 완료: {len(df)}행")
            finally:
                cursor.close()
                conn.close()
            
            if df.empty:
                print("⚠️ 데이터가 없습니다. 샘플 데이터를 생성합니다...")
                df = generate_sample_data(tab_id)
        
        memory_db.store_data(f"{tab_id}_data", df)
        
        # 기본 차트 생성
        charts = []
        
        if tab_id == "tab1" and not df.empty:
            # 연도별 평균 레이팅
            yearly_avg = df.groupby('year')['rating'].mean().reset_index()
            chart_config = convert_to_chartjs_format(yearly_avg, "line")
            if chart_config:
                chart_config["options"]["plugins"]["title"] = {
                    "display": True,
                    "text": "연도별 평균 레이팅 추이"
                }
                charts.append({
                    "id": f"{tab_id}_chart_1",
                    "config": chart_config,
                    "raw_data": yearly_avg.to_dict('records')
                })
            
            # 카테고리별 매출
            category_sales = df.groupby('category')['sales'].sum().reset_index()
            chart_config = convert_to_chartjs_format(category_sales, "doughnut")
            if chart_config:
                chart_config["options"]["plugins"]["title"] = {
                    "display": True,
                    "text": "카테고리별 총 매출"
                }
                charts.append({
                    "id": f"{tab_id}_chart_2",
                    "config": chart_config,
                    "raw_data": category_sales.to_dict('records')
                })
        
        elif tab_id == "tab2" and not df.empty:
            # 카테고리별 제품 수
            category_count = df.groupby('category').size().reset_index(name='count')
            chart_config = convert_to_chartjs_format(category_count, "bar")
            if chart_config:
                chart_config["options"]["plugins"]["title"] = {
                    "display": True,
                    "text": "카테고리별 제품 수"
                }
                charts.append({
                    "id": f"{tab_id}_chart_1",
                    "config": chart_config,
                    "raw_data": category_count.to_dict('records')
                })
        
        elif tab_id == "tab3" and not df.empty:
            # 지역별 고객 수
            region_count = df.groupby('region').size().reset_index(name='count')
            chart_config = convert_to_chartjs_format(region_count, "pie")
            if chart_config:
                chart_config["options"]["plugins"]["title"] = {
                    "display": True,
                    "text": "지역별 고객 분포"
                }
                charts.append({
                    "id": f"{tab_id}_chart_1",
                    "config": chart_config,
                    "raw_data": region_count.to_dict('records')
                })
        
        return {
            "success": True,
            "charts": charts,
            "total_rows": len(df)
        }
        
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"데이터 로드 실패: {str(e)}"
        )

# 사용자별 LLM 쿼리 처리
@app.post("/api/users/{username}/llm/query")
async def process_user_llm_query(
    username: str,
    query: LLMQuery
):
    """사용자별 LLM 쿼리 처리 (히스토리 저장 포함)"""
    try:
        # 테이블 존재 여부 확인
        table_name = f"{query.tab_id}_data"
        if not memory_db.table_exists(table_name):
            print(f"📊 {table_name} 테이블이 없어서 데이터를 로드합니다...")
            
            if TEST_MODE:
                print("🧪 테스트 모드: 샘플 데이터 생성")
                df = generate_sample_data(query.tab_id)
            else:
                conn = get_oracle_connection()
                cursor = conn.cursor()
                try:
                    check_and_create_tables(conn)
                    df = pd.read_sql(TAB_QUERIES[query.tab_id], conn)
                    print(f"✅ 데이터 로드 완료: {len(df)}행")
                finally:
                    cursor.close()
                    conn.close()
                
                if df.empty:
                    print("⚠️ 데이터가 없습니다. 샘플 데이터를 생성합니다...")
                    df = generate_sample_data(query.tab_id)
            
            memory_db.store_data(table_name, df)
            print(f"✅ {table_name} 테이블 생성 완료")
        
        # LLM API 호출
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"""
        당신은 데이터 분석 전문가입니다. 사용자의 질문을 분석하여 적절한 SQL 쿼리를 생성하거나 텍스트로 답변해주세요.
        
        현재 사용 가능한 테이블: {table_name}
        테이블 스키마: {memory_db.get_table_info(table_name)}
        
        응답은 반드시 다음 JSON 형식으로 해주세요:
        {{
            "chart_request": 1 또는 0,
            "sql_query": "SQL 쿼리 문자열",
            "chart_type": "bar/line/pie/doughnut/scatter",
            "description": "설명 텍스트"
        }}
        """
        
        payload = {
            "model": "your-model-name",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.question}
            ],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
        llm_response = response.json()
        content = llm_response["choices"][0]["message"]["content"]
        
        # JSON 파싱
        try:
            result = json.loads(content)
        except:
            result = {
                "chart_request": 0,
                "description": content
            }
        
        # 차트 요청인 경우 처리
        if result.get("chart_request") == 1:
            sql_query = result.get("sql_query", "")
            
            # SQL 인젝션 방지
            forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER"]
            if any(keyword in sql_query.upper() for keyword in forbidden_keywords):
                raise HTTPException(status_code=400, detail="허용되지 않은 SQL 명령어입니다")
            
            # 쿼리 실행
            df = memory_db.execute_query(sql_query)
            
            # Chart.js 형식으로 변환
            chart_config = convert_to_chartjs_format(df, result.get("chart_type", "bar"))
            
            if chart_config:
                chart_config["options"]["plugins"]["title"] = {
                    "display": True,
                    "text": query.question[:50] + "..."
                }
                
                response_data = {
                    "success": True,
                    "chart_request": 1,
                    "chart_config": chart_config,
                    "raw_data": df.to_dict('records'),
                    "description": result.get("description", ""),
                    "sql_query": sql_query,
                    "chart_type": result.get("chart_type", "bar")
                }
            else:
                response_data = {
                    "success": True,
                    "chart_request": 0,
                    "description": "차트 생성에 실패했습니다."
                }
        else:
            response_data = {
                "success": True,
                "chart_request": 0,
                "description": result.get("description", "질문에 대한 답변을 생성할 수 없습니다.")
            }
        
        # 히스토리 저장
        query_data = {
            "tab_id": query.tab_id,
            "question": query.question,
            "response": response_data,
            "chart_generated": response_data.get("chart_request") == 1
        }
        
        query_id = session_manager.save_query_history(username, query_data)
        response_data["query_id"] = query_id
        
        # 사용자 통계 업데이트
        user_info = session_manager.get_or_create_user(username)
        user_info["total_queries"] += 1
        if query_data["chart_generated"]:
            user_info["total_charts"] += 1
        session_manager.save_metadata(username, user_info)
        
        return response_data
        
    except Exception as e:
        print(f"❌ 쿼리 처리 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"쿼리 처리 실패: {str(e)}")

# ==================
# 프리셋 API 엔드포인트
# ==================

@app.get("/api/users/{username}/presets")
async def get_user_presets(
    username: str = FastPath(..., description="사용자명"),
    tab_id: str = None
):
    """사용자 프리셋 목록 조회"""
    try:
        preset_manager = PresetManager(username)
        presets = preset_manager.get_preset_list(tab_id)
        return {
            "success": True,
            "presets": presets
        }
    except Exception as e:
        print(f"❌ 프리셋 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프리셋 목록 조회 실패: {str(e)}")

@app.post("/api/users/{username}/presets")
async def create_user_preset(
    username: str = FastPath(..., description="사용자명"),
    preset_data: PresetCreate = Body(...)
):
    """새 프리셋 생성"""
    try:
        preset_manager = PresetManager(username)
        preset_id = preset_manager.save_preset(preset_data.dict())
        return {
            "success": True,
            "preset_id": preset_id,
            "message": "프리셋이 성공적으로 저장되었습니다."
        }
    except Exception as e:
        print(f"❌ 프리셋 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프리셋 생성 실패: {str(e)}")

@app.get("/api/users/{username}/presets/{preset_id}")
async def get_user_preset(
    username: str = FastPath(..., description="사용자명"),
    preset_id: str = FastPath(..., description="프리셋 ID")
):
    """프리셋 로드 (차트 데이터 포함)"""
    try:
        preset_manager = PresetManager(username)
        result = preset_manager.load_preset(preset_id)
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 프리셋 로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프리셋 로드 실패: {str(e)}")

@app.put("/api/users/{username}/presets/{preset_id}")
async def update_user_preset(
    username: str = FastPath(..., description="사용자명"),
    preset_id: str = FastPath(..., description="프리셋 ID"),
    update_data: PresetUpdate = Body(...)
):
    """프리셋 수정"""
    try:
        preset_manager = PresetManager(username)
        success = preset_manager.update_preset(preset_id, update_data.dict(exclude_unset=True))
        
        if not success:
            raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다")
        
        return {
            "success": True,
            "message": "프리셋이 성공적으로 수정되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 프리셋 수정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프리셋 수정 실패: {str(e)}")

@app.delete("/api/users/{username}/presets/{preset_id}")
async def delete_user_preset(
    username: str = FastPath(..., description="사용자명"),
    preset_id: str = FastPath(..., description="프리셋 ID")
):
    """프리셋 삭제"""
    try:
        preset_manager = PresetManager(username)
        success = preset_manager.delete_preset(preset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="프리셋을 찾을 수 없습니다")
        
        return {
            "success": True,
            "message": "프리셋이 성공적으로 삭제되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 프리셋 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프리셋 삭제 실패: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
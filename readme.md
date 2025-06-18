# LLM 기반 차트 시각화 시스템

자연어 질문을 통해 데이터를 분석하고 차트를 생성하는 웹 애플리케이션입니다. 사용자는 복잡한 SQL을 작성할 필요 없이 일상 언어로 데이터에 대해 질문하고, 실시간으로 시각화된 결과를 얻을 수 있습니다.

## 🚀 주요 기능

### 1. 자연어 기반 데이터 분석
- **LLM 채팅 인터페이스**: "2024년 매출 추이를 보여줘"와 같은 자연어 질문
- **자동 SQL 생성**: LLM이 질문을 분석하여 적절한 SQL 쿼리 생성
- **실시간 차트 생성**: Chart.js를 사용한 인터랙티브 차트 자동 생성

### 2. 직관적인 차트 관리
- **드래그 앤 드롭**: 차트 위치 변경 및 내용 교체
- **+ 버튼 추가**: LLM 결과를 그리드에 간편 추가
- **데이터 조회**: 차트 hover 시 원본 데이터 테이블 확인

### 3. 프리셋 시스템
- **현재 상태 저장**: 차트 조합을 프리셋으로 저장
- **빠른 복원**: 저장된 프리셋을 클릭으로 불러오기
- **쿼리 참조 방식**: 메모리 효율적인 데이터 관리

### 4. 사용자별 히스토리 관리
- **쿼리 기록**: 모든 질문과 답변 자동 저장
- **상세 보기**: 과거 쿼리의 SQL, 차트, 데이터 확인
- **사용자 통계**: 총 쿼리 수, 생성 차트 수 추적

## 🛠️ 기술 스택

### Frontend (React)
- **React 18**: 메인 프레임워크
- **Chart.js**: 차트 렌더링 엔진
- **React Router**: SPA 라우팅
- **Tailwind CSS**: 반응형 UI 스타일링
- **Lucide Icons**: 아이콘 시스템

### Backend (FastAPI)
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Oracle DB**: 운영 데이터베이스 (테스트 모드 지원)
- **SQLite**: 인메모리 쿼리 실행
- **Pandas**: 데이터 처리 및 변환
- **httpx**: 비동기 HTTP 클라이언트 (LLM API 통신)

### Data Storage
- **파일 기반**: 사용자 데이터, 히스토리, 프리셋
- **JSON 구조**: 구조화된 데이터 저장
- **참조 시스템**: 중복 방지를 위한 쿼리 참조

## 📁 프로젝트 구조

```
project/
├── src/
│   ├── App.js                 # 메인 React 컴포넌트
│   └── UserApp.js            # 사용자별 라우팅 시스템
├── main.py                   # FastAPI 백엔드 서버
├── user_data/               # 사용자 데이터 저장소
│   └── {username}/
│       ├── metadata.json    # 사용자 메타데이터
│       ├── history_index.json # 히스토리 인덱스
│       ├── queries/         # 쿼리 기록
│       │   ├── 20250618_181954_b4eb76de.json
│       │   └── ...
│       └── presets/         # 프리셋 저장소
│           ├── preset_index.json
│           ├── preset_20250618_185320.json
│           └── ...
└── README.md
```

## 🎯 사용자 워크플로우

### 1. 기본 사용 흐름
```mermaid
graph LR
A[사용자 접속] --> B[탭 선택]
B --> C[기본 차트 확인]
C --> D[LLM 채팅 열기]
D --> E[자연어 질문]
E --> F[차트 생성]
F --> G[그리드에 추가]
G --> H[프리셋 저장]
```

### 2. 차트 조작 방법
- **➕ 추가**: LLM 채팅 차트에 마우스 hover → + 버튼 클릭
- **📍 위치 변경**: 그리드 차트를 다른 위치로 드래그
- **🔄 내용 교체**: LLM 차트를 기존 차트로 드래그 → 확인
- **💾 프리셋 저장**: "현재 저장" 버튼으로 상태 저장

## 🚦 설치 및 실행

### 환경 요구사항
- Python 3.8+
- Node.js 16+
- Oracle DB (선택사항, 테스트 모드 지원)

### 백엔드 설정
```bash
# 의존성 설치
pip install fastapi uvicorn pandas oracledb httpx

# 환경변수 설정 (선택사항)
export TEST_MODE=true  # 테스트 모드 활성화
export API_KEY=your_llm_api_key

# 서버 실행
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 설정
```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

### 접속 URL
- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

## 📊 데이터 구조

### 쿼리 히스토리 형식
```json
{
  "id": "20250618_181954_b4eb76de",
  "timestamp": "2025-06-18T18:19:54.462302",
  "tab_id": "tab1",
  "question": "2024년 매출",
  "response": {
    "success": true,
    "chart_request": 1,
    "chart_config": {
      "type": "line",
      "data": { /* Chart.js 데이터 */ },
      "options": { /* Chart.js 옵션 */ }
    },
    "raw_data": [ /* 원본 데이터 배열 */ ],
    "description": "2024년 분기별 총 매출을 분석했습니다.",
    "sql_query": "SELECT quarter, SUM(sales) as total_sales FROM tab1_data WHERE year = 2024 GROUP BY quarter ORDER BY quarter"
  },
  "chart_generated": true
}
```

### 프리셋 형식
```json
{
  "id": "preset_20250618_185320_b030a25f",
  "name": "매출 분석 대시보드",
  "description": "2024년 매출 관련 차트 모음",
  "tab_id": "tab1",
  "created_at": "2025-06-18T18:53:20Z",
  "grid_config": {
    "layout": "grid-cols-2",
    "charts": [
      {
        "position": 0,
        "source": {
          "type": "query_reference",
          "query_id": "20250618_181954_b4eb76de",
          "title": "분기별 매출 추이"
        }
      }
    ]
  }
}
```

## 🔧 API 엔드포인트

### 데이터 관련
- `GET /api/tabs/{tab_id}/data` - 탭 데이터 로드
- `POST /api/users/{username}/llm/query` - LLM 쿼리 처리

### 사용자 관리
- `GET /api/users/{username}/info` - 사용자 정보
- `GET /api/users/{username}/history` - 쿼리 히스토리
- `GET /api/users/{username}/history/{query_id}` - 히스토리 상세

### 프리셋 관리
- `GET /api/users/{username}/presets` - 프리셋 목록
- `POST /api/users/{username}/presets` - 프리셋 생성
- `GET /api/users/{username}/presets/{preset_id}` - 프리셋 로드
- `PUT /api/users/{username}/presets/{preset_id}` - 프리셋 수정
- `DELETE /api/users/{username}/presets/{preset_id}` - 프리셋 삭제

## 🎨 UI/UX 특징

### 반응형 디자인
- **모바일 최적화**: 터치 인터페이스 지원
- **다크 모드**: 자동 다크 모드 대응
- **접근성**: 키보드 내비게이션 지원

### 시각적 피드백
- **드래그 앤 드롭**: 실시간 시각적 피드백
- **로딩 상태**: 스피너와 진행 표시
- **애니메이션**: 부드러운 전환 효과

### 에러 처리
- **사용자 친화적**: 기술적 오류를 일반 언어로 설명
- **복구 옵션**: 실패 시 대안 제시
- **로그 시스템**: 개발자를 위한 상세 로그

## ⚙️ 설정 옵션

### 환경 변수
```bash
# 테스트 모드 (Oracle DB 없이 실행)
TEST_MODE=true

# LLM API 설정
LLM_API_KEY=your_api_key
LLM_API_URL=http://your-llm-server.com/v1/chat/completions

# Oracle DB 설정
ORACLE_USER=system
ORACLE_PASSWORD=password
ORACLE_DSN=localhost:1521/XE
```

### 탭 설정 (main.py)
```python
TAB_QUERIES = {
    "tab1": "SELECT year, quarter, category, rating, sales FROM performance_data WHERE year >= 2022",
    "tab2": "SELECT product_id, product_name, category, price, stock FROM products WHERE status = 'active'",
    "tab3": "SELECT customer_id, region, total_orders, satisfaction_score FROM customer_metrics"
}
```

## 🔒 보안 고려사항

### SQL 인젝션 방지
- **키워드 필터링**: DROP, DELETE 등 위험 명령어 차단
- **쿼리 검증**: LLM 생성 쿼리 사전 검증
- **읽기 전용**: SELECT 쿼리만 허용

### 데이터 보호
- **사용자 분리**: 개별 폴더로 데이터 격리
- **입력 검증**: 모든 사용자 입력 검증
- **에러 마스킹**: 민감한 정보가 포함된 에러 메시지 숨김

## 🚧 알려진 제한사항

1. **LLM 의존성**: LLM API 서버가 필요
2. **언어 지원**: 현재 한국어 중심
3. **차트 타입**: Chart.js 지원 범위 내
4. **동시성**: 파일 기반 저장소의 동시 접근 제한


---

**💡 팁**: 첫 실행 시 테스트 모드(`TEST_MODE=true`)로 시작하여 샘플 데이터로 기능을 확인해보세요!
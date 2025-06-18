// UserApp.js - 사용자별 라우팅을 추가한 App 컴포넌트
import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Route, Routes, useParams, useNavigate, Navigate } from 'react-router-dom';
import Chart from 'chart.js/auto';
import App from './App'; // 기존 App 컴포넌트

// 사용자 정보를 표시하는 헤더 컴포넌트
const UserHeader = ({ username, userInfo }) => {
  const navigate = useNavigate();
  
  return (
    <div className="bg-blue-600 text-white px-4 py-2 text-sm">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span>👤 {username}</span>
          {userInfo && (
            <>
              <span>📊 쿼리: {userInfo.total_queries}</span>
              <span>📈 차트: {userInfo.total_charts}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(`/history/${username}`)}
            className="hover:underline"
          >
            📜 히스토리
          </button>
        </div>
      </div>
    </div>
  );
};

// 사용자별 앱 래퍼
const UserApp = () => {
  const { username } = useParams();
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    // 사용자 정보 로드
    fetch(`http://localhost:8000/api/users/${username}/info`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setUserInfo(data.user);
        }
      })
      .catch(err => console.error('Failed to load user info:', err));
  }, [username]);

  // API URL을 사용자별로 수정
  const apiUrl = `http://localhost:8000/api/users/${username}`;

  return (
    <div>
      <UserHeader username={username} userInfo={userInfo} />
      <App username={username} apiUrl={apiUrl} />
    </div>
  );
};

// 히스토리 페이지
const HistoryPage = () => {
  const { username } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/users/${username}/history?limit=50`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setHistory(data.history);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load history:', err);
        setLoading(false);
      });
  }, [username]);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">
            {username}님의 쿼리 히스토리
          </h1>
          <button
            onClick={() => navigate(`/${username}`)}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            ← 메인으로
          </button>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-600">로딩 중...</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {history.map((item) => (
              <div 
                key={item.id} 
                className="bg-white p-4 rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(`/history/${username}/${item.id}`)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <p className="font-medium text-gray-800 line-clamp-2">
                      {item.question}
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      {new Date(item.timestamp).toLocaleString('ko-KR')}
                    </p>
                  </div>
                </div>
                {item.chart_generated && (
                  <div className="mt-3 flex items-center justify-between">
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                      차트 생성됨
                    </span>
                    <span className="text-blue-600 text-sm hover:underline">
                      상세보기 →
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {!loading && history.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            <p>아직 히스토리가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// 히스토리 상세 페이지 (쿼리 상세 및 차트 표시)
const HistoryDetailPage = () => {
  const { username, queryId } = useParams();
  const navigate = useNavigate();
  const [queryData, setQueryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    // 쿼리 데이터 로드
    fetch(`http://localhost:8000/api/users/${username}/history/${queryId}`)
      .then(res => {
        if (!res.ok) throw new Error('쿼리를 찾을 수 없습니다');
        return res.json();
      })
      .then(data => {
        if (data.success) {
          setQueryData(data.query);
        } else {
          throw new Error('쿼리 로드 실패');
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load query:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [username, queryId]);

  useEffect(() => {
    // Chart.js로 차트 렌더링
    if (queryData && queryData.response && queryData.response.chart_config && canvasRef.current) {
      // 기존 차트 제거
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }

      try {
        const ctx = canvasRef.current.getContext('2d');
        chartInstanceRef.current = new Chart(ctx, {
          type: queryData.response.chart_config.type,
          data: queryData.response.chart_config.data,
          options: queryData.response.chart_config.options || {}
        });
      } catch (error) {
        console.error('Chart rendering error:', error);
        setError('차트 렌더링 오류');
      }
    }

    // Cleanup
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [queryData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">쿼리 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">오류</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const hasChart = queryData?.response?.chart_request === 1;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">쿼리 상세 정보</h1>
            <button
              onClick={() => navigate(`/history/${username}`)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              ← 히스토리로
            </button>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <span>사용자: {username}</span>
            <span className="mx-2">|</span>
            <span>쿼리 ID: {queryId}</span>
            <span className="mx-2">|</span>
            <span>생성일: {new Date(queryData.timestamp).toLocaleString('ko-KR')}</span>
          </div>
        </div>

        {/* 질문과 답변 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">질문</h2>
          <p className="text-gray-800 mb-4">{queryData.question}</p>
          
          <h2 className="text-lg font-semibold mb-4">답변</h2>
          <p className="text-gray-800">{queryData.response?.description || '답변 없음'}</p>
        </div>

        {hasChart ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 차트 영역 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold mb-4">차트</h2>
              <div className="h-96">
                <canvas ref={canvasRef}></canvas>
              </div>
            </div>

            {/* SQL 및 데이터 정보 */}
            <div className="space-y-6">
              {/* SQL 쿼리 */}
              {queryData.response.sql_query && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h2 className="text-lg font-semibold mb-4">SQL 쿼리</h2>
                  <div className="bg-gray-50 p-4 rounded">
                    <code className="text-sm text-gray-800 whitespace-pre-wrap">
                      {queryData.response.sql_query}
                    </code>
                  </div>
                </div>
              )}

              {/* 차트 설정 */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-lg font-semibold mb-4">차트 정보</h2>
                <dl className="space-y-2">
                  <div className="flex">
                    <dt className="font-medium text-gray-600 w-24">차트 타입:</dt>
                    <dd className="text-gray-800">{queryData.response.chart_type || 'N/A'}</dd>
                  </div>
                  <div className="flex">
                    <dt className="font-medium text-gray-600 w-24">탭 ID:</dt>
                    <dd className="text-gray-800">{queryData.tab_id}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded">
            <p>이 쿼리는 차트를 생성하지 않았습니다.</p>
          </div>
        )}

        {/* 원본 데이터 테이블 */}
        {hasChart && queryData.response.raw_data && queryData.response.raw_data.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">원본 데이터</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    {Object.keys(queryData.response.raw_data[0]).map((key) => (
                      <th key={key} className="border border-gray-300 px-4 py-2 text-left text-sm font-medium">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {queryData.response.raw_data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      {Object.values(row).map((value, cellIdx) => (
                        <td key={cellIdx} className="border border-gray-300 px-4 py-2 text-sm">
                          {value !== null && value !== undefined ? value.toString() : ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              총 {queryData.response.raw_data.length}개 행
            </p>
          </div>
        )}

        {/* 전체 응답 데이터 (개발자용) */}
        <details className="mt-6 bg-white rounded-lg shadow-md p-6">
          <summary className="cursor-pointer font-semibold text-lg">
            전체 응답 데이터 (개발자용)
          </summary>
          <div className="mt-4 bg-gray-50 p-4 rounded overflow-auto max-h-96">
            <pre className="text-xs">
              {JSON.stringify(queryData, null, 2)}
            </pre>
          </div>
        </details>
      </div>
    </div>
  );
};

// 랜딩 페이지 (사용자 선택)
const LandingPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [recentUsers, setRecentUsers] = useState([]);

  useEffect(() => {
    // 로컬 스토리지에서 최근 사용자 목록 가져오기
    const users = JSON.parse(localStorage.getItem('recentUsers') || '[]');
    setRecentUsers(users);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username.trim()) {
      // 최근 사용자 목록 업데이트
      const users = [username, ...recentUsers.filter(u => u !== username)].slice(0, 5);
      localStorage.setItem('recentUsers', JSON.stringify(users));
      
      // 사용자 페이지로 이동
      navigate(`/${username}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold mb-6 text-center">
          LLM 차트 시각화 시스템
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              사용자 이름
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="이름을 입력하세요"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>
          
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            시작하기
          </button>
        </form>
        
        {recentUsers.length > 0 && (
          <div className="mt-6">
            <p className="text-sm text-gray-600 mb-2">최근 사용자:</p>
            <div className="flex flex-wrap gap-2">
              {recentUsers.map((user) => (
                <button
                  key={user}
                  onClick={() => navigate(`/${user}`)}
                  className="px-3 py-1 bg-gray-100 rounded-full text-sm hover:bg-gray-200"
                >
                  {user}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 차트 상세 페이지
const ChartDetailPage = () => {
  const { username, chartId } = useParams();
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const canvasRef = useRef(null);
  const chartInstanceRef = useRef(null);

  useEffect(() => {
    // 차트 데이터 로드
    fetch(`http://localhost:8000/api/users/${username}/charts/${chartId}`)
      .then(res => {
        if (!res.ok) throw new Error('차트를 찾을 수 없습니다');
        return res.json();
      })
      .then(data => {
        if (data.success) {
          setChartData(data.chart);
        } else {
          throw new Error('차트 로드 실패');
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load chart:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [username, chartId]);

  useEffect(() => {
    // Chart.js로 차트 렌더링
    if (chartData && chartData.config && canvasRef.current) {
      // 기존 차트 제거
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }

      try {
        const ctx = canvasRef.current.getContext('2d');
        chartInstanceRef.current = new Chart(ctx, {
          type: chartData.config.type,
          data: chartData.config.data,
          options: chartData.config.options || {}
        });
      } catch (error) {
        console.error('Chart rendering error:', error);
        setError('차트 렌더링 오류');
      }
    }

    // Cleanup
    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [chartData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">차트 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">오류</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">차트 상세 정보</h1>
            <button
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              ← 뒤로가기
            </button>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            <span>사용자: {username}</span>
            <span className="mx-2">|</span>
            <span>차트 ID: {chartId}</span>
            <span className="mx-2">|</span>
            <span>생성일: {new Date(chartData.timestamp).toLocaleString('ko-KR')}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 차트 영역 */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">차트</h2>
            <div className="h-96">
              <canvas ref={canvasRef}></canvas>
            </div>
          </div>

          {/* 메타데이터 영역 */}
          <div className="space-y-6">
            {/* 기본 정보 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold mb-4">기본 정보</h2>
              <dl className="space-y-2">
                <div className="flex">
                  <dt className="font-medium text-gray-600 w-24">탭 ID:</dt>
                  <dd className="text-gray-800">{chartData.tab_id}</dd>
                </div>
                <div className="flex">
                  <dt className="font-medium text-gray-600 w-24">차트 타입:</dt>
                  <dd className="text-gray-800">{chartData.config?.type || 'N/A'}</dd>
                </div>
                {chartData.query_id && (
                  <div className="flex">
                    <dt className="font-medium text-gray-600 w-24">쿼리 ID:</dt>
                    <dd className="text-gray-800 text-sm">{chartData.query_id}</dd>
                  </div>
                )}
              </dl>
            </div>

            {/* 차트 설정 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold mb-4">차트 설정 (JSON)</h2>
              <div className="bg-gray-50 p-4 rounded overflow-auto max-h-96">
                <pre className="text-xs">
                  {JSON.stringify(chartData.config, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* 원본 데이터 테이블 */}
        {chartData.raw_data && chartData.raw_data.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">원본 데이터</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    {Object.keys(chartData.raw_data[0]).map((key) => (
                      <th key={key} className="border border-gray-300 px-4 py-2 text-left text-sm font-medium">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {chartData.raw_data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      {Object.values(row).map((value, cellIdx) => (
                        <td key={cellIdx} className="border border-gray-300 px-4 py-2 text-sm">
                          {value !== null && value !== undefined ? value.toString() : ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              총 {chartData.raw_data.length}개 행
            </p>
          </div>
        )}

        {/* 전체 JSON 데이터 (개발자용) */}
        <details className="mt-6 bg-white rounded-lg shadow-md p-6">
          <summary className="cursor-pointer font-semibold text-lg">
            전체 JSON 데이터 (개발자용)
          </summary>
          <div className="mt-4 bg-gray-50 p-4 rounded overflow-auto max-h-96">
            <pre className="text-xs">
              {JSON.stringify(chartData, null, 2)}
            </pre>
          </div>
        </details>
      </div>
    </div>
  );
};

// 메인 라우터
const MainRouter = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/:username" element={<UserApp />} />
        <Route path="/history/:username" element={<HistoryPage />} />
        <Route path="/history/:username/:queryId" element={<HistoryDetailPage />} />
      </Routes>
    </Router>
  );
};

export default MainRouter;
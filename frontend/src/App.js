// src/App.js
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Chart from 'chart.js/auto';
import { MessageCircle, X, Plus, Table, Loader2, AlertCircle, Move, Save, FolderOpen, Edit2, Trash2 } from 'lucide-react';
import { BrowserRouter as Router, Route, Routes, useParams, useNavigate, Navigate } from 'react-router-dom';

// 드래그 타입 구분
const DRAG_TYPES = {
  REORDER: 'reorder',
  REPLACE: 'replace'
};

// 프리셋 저장 모달
const SavePresetModal = ({ isOpen, onSave, onClose }) => {
  const [presetName, setPresetName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!presetName.trim()) return;

    setLoading(true);
    try {
      await onSave(presetName.trim(), description.trim());
      setPresetName('');
      setDescription('');
      onClose();
    } catch (error) {
      console.error('프리셋 저장 실패:', error);
      alert('프리셋 저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPresetName('');
    setDescription('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <Save className="text-blue-500" size={24} />
          <h3 className="text-lg font-semibold">프리셋 저장</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프리셋 이름 *
            </label>
            <input
              type="text"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="예: 매출 분석 대시보드"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              설명 (선택사항)
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="프리셋에 대한 간단한 설명을 입력하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              취소
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 flex items-center justify-center gap-2"
              disabled={loading || !presetName.trim()}
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={16} />
                  저장 중...
                </>
              ) : (
                '저장하기'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// 확인 모달 컴포넌트
const ConfirmModal = ({ isOpen, title, message, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-500" size={24} />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        
        <p className="text-gray-700 mb-6">{message}</p>
        
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  );
};

// 프리셋 선택 드롭다운
const PresetSelector = ({ presets, loading, onLoad, onSave, onDelete }) => {
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState({ isOpen: false, presetId: null, presetName: '' });

  const handleLoad = async (presetId) => {
    if (!presetId) return;
    try {
      await onLoad(presetId);
      setSelectedPreset('');
    } catch (error) {
      console.error('프리셋 로드 실패:', error);
      alert('프리셋 로드에 실패했습니다.');
    }
  };

  const handleDeleteClick = (presetId, presetName) => {
    setDeleteConfirm({
      isOpen: true,
      presetId,
      presetName
    });
  };

  const handleDeleteConfirm = async () => {
    try {
      await onDelete(deleteConfirm.presetId);
      setSelectedPreset('');
      setDeleteConfirm({ isOpen: false, presetId: null, presetName: '' });
    } catch (error) {
      console.error('프리셋 삭제 실패:', error);
      alert('프리셋 삭제에 실패했습니다.');
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirm({ isOpen: false, presetId: null, presetName: '' });
  };

  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          disabled={loading}
        >
          <FolderOpen size={16} />
          프리셋 ({presets.length})
          {loading && <Loader2 className="animate-spin" size={14} />}
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
            <div className="p-2 border-b border-gray-100">
              <div className="text-sm font-medium text-gray-700">저장된 프리셋</div>
            </div>
            
            <div className="max-h-64 overflow-y-auto">
              {presets.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-sm">
                  저장된 프리셋이 없습니다
                </div>
              ) : (
                presets.map((preset) => (
                  <div key={preset.id} className="p-3 hover:bg-gray-50 border-b border-gray-50 last:border-b-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <button
                          onClick={() => {
                            handleLoad(preset.id);
                            setIsOpen(false);
                          }}
                          className="text-left w-full"
                        >
                          <div className="font-medium text-sm truncate">{preset.name}</div>
                          {preset.description && (
                            <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                              {preset.description}
                            </div>
                          )}
                          <div className="text-xs text-gray-400 mt-1">
                            {preset.chart_count}개 차트 • {new Date(preset.created_at).toLocaleDateString()}
                          </div>
                        </button>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(preset.id, preset.name);
                        }}
                        className="ml-2 p-1 text-gray-400 hover:text-red-500"
                        title="삭제"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="p-2 border-t border-gray-100">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full text-center text-sm text-gray-500 hover:text-gray-700"
              >
                닫기
              </button>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={onSave}
        className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        disabled={loading}
      >
        <Save size={16} />
        현재 저장
      </button>

      {isOpen && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 삭제 확인 모달 */}
      <ConfirmModal
        isOpen={deleteConfirm.isOpen}
        title="프리셋 삭제"
        message={`"${deleteConfirm.presetName}" 프리셋을 정말 삭제하시겠습니까?`}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
      />
    </div>
  );
};

// 차트 교체 확인 모달
const ReplaceConfirmModal = ({ isOpen, sourceChart, targetChart, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-orange-500" size={24} />
          <h3 className="text-lg font-semibold">차트를 변경하시겠습니까?</h3>
        </div>
        
        <div className="space-y-3 mb-6">
          <div>
            <p className="text-sm text-gray-600">현재 차트:</p>
            <p className="font-medium">{targetChart?.title || '기존 차트'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">새 차트:</p>
            <p className="font-medium">{sourceChart?.title || '새로운 차트'}</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            변경하기
          </button>
        </div>
      </div>
    </div>
  );
};

// 개선된 차트 컴포넌트 - Chart.js 직접 사용 + 드래그 앤 드롭
const ChartComponent = ({ 
  chartData, 
  index,
  onShowData, 
  onRemove, 
  onAddToGrid,
  // 드래그 앤 드롭 관련 props
  isDragging,
  isDragOver,
  dragOverType,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  onDrop,
  isGridChart = false,
  isNewChart = false
}) => {
  const [showDataBtn, setShowDataBtn] = useState(false);
  const [isShaking, setIsShaking] = useState(false);
  const canvasRef = useRef(null);
  const chartRef = useRef(null);
  const hoverTimeoutRef = useRef(null);
  const shakeTimeoutRef = useRef(null);

  useEffect(() => {
    if (!chartData || !chartData.config || !canvasRef.current) {
      return;
    }

    // 기존 차트 제거
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    // 새 차트 생성
    try {
      const ctx = canvasRef.current.getContext('2d');
      
      // onHover 이벤트 추가
      const modifiedOptions = {
        ...chartData.config.options,
        onHover: (event, activeElements, chart) => {
          setShowDataBtn(true);
          // 기존 타임아웃 취소
          if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current);
          }
          // 2초 후 버튼 숨기기
          hoverTimeoutRef.current = setTimeout(() => {
            setShowDataBtn(false);
          }, 2000);
        }
      };

      chartRef.current = new Chart(ctx, {
        type: chartData.config.type,
        data: chartData.config.data,
        options: modifiedOptions
      });
    } catch (error) {
      console.error('Chart creation error:', error);
    }

    // Cleanup
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
      if (shakeTimeoutRef.current) {
        clearTimeout(shakeTimeoutRef.current);
      }
    };
  }, [chartData]);

  // 드래그 시작 처리
  const handleDragStart = (e) => {
    if (isGridChart && onDragStart) {
      e.dataTransfer.setData('chart', JSON.stringify({ 
        chart: chartData, 
        index, 
        type: DRAG_TYPES.REORDER,
        source: 'grid' 
      }));
      onDragStart(index);
    } else if (isNewChart) {
      e.dataTransfer.setData('chart', JSON.stringify({ 
        chart: chartData, 
        type: DRAG_TYPES.REPLACE,
        source: 'new' 
      }));
    }
  };

  // 드래그 오버 처리
  const handleDragOver = (e) => {
    e.preventDefault();
    
    if (!isGridChart || !onDragOver) return;
    
    // 드래그된 데이터 확인
    const dragData = e.dataTransfer.types.includes('chart');
    if (!dragData) return;

    // 흔들림 효과 시작
    if (!isShaking) {
      setIsShaking(true);
      if (shakeTimeoutRef.current) {
        clearTimeout(shakeTimeoutRef.current);
      }
      shakeTimeoutRef.current = setTimeout(() => {
        setIsShaking(false);
      }, 200);
    }

    onDragOver(index);
  };

  // 드래그 리브 처리
  const handleDragLeave = (e) => {
    e.preventDefault();
    if (!isGridChart || !onDragLeave) return;
    
    setIsShaking(false);
    if (shakeTimeoutRef.current) {
      clearTimeout(shakeTimeoutRef.current);
    }
    onDragLeave();
  };

  // 드롭 처리
  const handleDrop = (e) => {
    e.preventDefault();
    if (!isGridChart || !onDrop) return;
    
    setIsShaking(false);
    if (shakeTimeoutRef.current) {
      clearTimeout(shakeTimeoutRef.current);
    }
    
    try {
      const draggedData = JSON.parse(e.dataTransfer.getData('chart'));
      onDrop(index, draggedData);
    } catch (error) {
      console.error('Drop data parsing error:', error);
    }
  };

  // 드래그 오버 상태에 따른 스타일 결정
  const getDropZoneStyle = () => {
    if (!isDragOver) return '';
    
    switch (dragOverType) {
      case DRAG_TYPES.REORDER:
        return 'border-4 border-dashed border-blue-500 bg-blue-50';
      case DRAG_TYPES.REPLACE:
        return 'border-4 border-dashed border-orange-500 bg-orange-50';
      default:
        return 'border-4 border-dashed border-gray-400 bg-gray-50';
    }
  };

  if (!chartData || !chartData.config) {
    return <div className="text-gray-500 text-center p-4">차트 데이터가 없습니다.</div>;
  }

  return (
    <div 
      className={`relative bg-white rounded-lg shadow-md p-4 h-full transition-all duration-200 ${
        isDragging ? 'opacity-50 transform rotate-2 scale-95' : ''
      } ${isShaking ? 'animate-pulse scale-105' : ''} ${getDropZoneStyle()}`}
      draggable={isGridChart || isNewChart}
      onDragStart={handleDragStart}
      onDragEnd={onDragEnd}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* 드래그 핸들 (그리드 차트용) */}
      {isGridChart && (
        <div className="absolute top-2 left-2 cursor-move opacity-0 hover:opacity-100 transition-opacity z-10">
          <Move className="text-gray-400 hover:text-gray-600" size={16} />
        </div>
      )}

      <div className="h-full">
        <canvas ref={canvasRef}></canvas>
      </div>
      
      {/* 호버 시 나타나는 버튼들 */}
      {showDataBtn && (
        <div className="absolute top-2 right-2 flex gap-2">
          <button
            onClick={() => onShowData(chartData.raw_data)}
            className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 flex items-center gap-1"
          >
            <Table size={16} />
            데이터 조회
          </button>
          {onAddToGrid && (
            <button
              onClick={() => onAddToGrid(chartData)}
              className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 flex items-center gap-1"
            >
              <Plus size={16} />
            </button>
          )}
        </div>
      )}
      
      {/* 제거 버튼 */}
      {onRemove && (
        <button
          onClick={onRemove}
          className="absolute top-2 left-2 bg-red-500 text-white p-1 rounded hover:bg-red-600"
        >
          <X size={16} />
        </button>
      )}

      {/* 드래그 오버 표시 */}
      {isDragOver && (
        <div className="absolute inset-0 bg-blue-500 bg-opacity-10 rounded-lg flex items-center justify-center">
          <div className="bg-white px-3 py-1 rounded shadow text-sm font-medium">
            {dragOverType === DRAG_TYPES.REORDER ? '📍 위치 변경' : '🔄 차트 교체'}
          </div>
        </div>
      )}

      {/* 새 차트 드래그 안내 */}
      {isNewChart && (
        <div className="absolute bottom-2 left-2 right-2">
          <div className="text-xs text-gray-500 bg-gray-50 rounded px-2 py-1 text-center">
            🖱️ + 버튼으로 추가 또는 드래그하여 교체
          </div>
        </div>
      )}
    </div>
  );
};

// 데이터 테이블 모달
const DataTableModal = ({ data, columns, onClose }) => {
  if (!data || data.length === 0) return null;

  const tableColumns = columns || Object.keys(data[0]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">데이터 상세</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>
        
        <table className="min-w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-100">
              {tableColumns.map((col, idx) => (
                <th key={idx} className="border border-gray-300 px-4 py-2 text-left">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {tableColumns.map((col, colIdx) => (
                  <td key={colIdx} className="border border-gray-300 px-4 py-2">
                    {row[col]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// LLM 채팅 패널
const LLMChatPanel = ({ isOpen, onClose, currentTab, username, apiUrl }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // 사용자별 엔드포인트 사용
      const endpoint = username 
        ? `${apiUrl}/llm/query`  // apiUrl에 이미 /api/users/{username} 포함
        : `${apiUrl}/api/llm/query`;
        
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMessage,
          tab_id: currentTab
        })
      });

      if (!response.ok) throw new Error('LLM 요청 실패');
      
      const data = await response.json();
      
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.description,
        chartData: data.chart_request === 1 ? {
          config: data.chart_config,
          raw_data: data.raw_data,
          title: userMessage, // 질문을 제목으로 사용
          query_id: data.query_id // 쿼리 ID 포함
        } : null
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: `오류 발생: ${error.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const addChartToGrid = (chartData) => {
    window.dispatchEvent(new CustomEvent('addChartToGrid', { detail: chartData }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg transition-all duration-300 h-96 z-40">
      <div className="flex flex-col h-full">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-semibold">LLM 데이터 분석</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[70%] ${
                msg.type === 'user' ? 'bg-blue-500 text-white' : 
                msg.type === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100'
              } rounded-lg p-3`}>
                {msg.chartData ? (
                  <div className="space-y-2">
                    <p className="mb-2">{msg.content}</p>
                    <div className="h-64 bg-white rounded p-2">
                      <ChartComponent
                        chartData={msg.chartData}
                        onShowData={(data) => {
                          window.dispatchEvent(new CustomEvent('showDataTable', { detail: data }));
                        }}
                        onAddToGrid={addChartToGrid}
                        isNewChart={true}
                      />
                    </div>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3 flex items-center gap-2">
                <Loader2 className="animate-spin" size={16} />
                <span>분석 중...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !loading && input.trim()) {
                  handleSubmit();
                }
              }}
              placeholder="데이터에 대해 질문해보세요..."
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleSubmit}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              전송
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// 프리셋 관리 훅
const usePresets = (username, apiUrl, activeTab) => {
  const [presets, setPresets] = useState([]);
  const [loading, setLoading] = useState(false);

  // API URL 정리 함수
  const getApiUrl = (endpoint) => {
    // apiUrl이 이미 /api/users/{username} 형태라면 그대로 사용
    if (apiUrl && apiUrl.includes('/api/users/')) {
      return `${apiUrl}${endpoint}`;
    }
    // 기본 API URL인 경우
    return `${apiUrl}/api/users/${username}${endpoint}`;
  };

  const loadPresets = useCallback(async () => {
    if (!username) return;
    
    setLoading(true);
    try {
      const url = getApiUrl(`/presets?tab_id=${activeTab}`);
      console.log('프리셋 로드 URL:', url); // 디버깅용
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setPresets(data.presets || []);
      } else {
        console.error('프리셋 로드 실패:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('프리셋 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }, [username, apiUrl, activeTab]);

  const savePreset = useCallback(async (name, description, currentCharts) => {
    if (!username) return;

    const presetData = {
      name,
      description,
      tab_id: activeTab,
      grid_config: {
        layout: `grid-cols-${Math.ceil(Math.sqrt(currentCharts.length))}`,
        charts: currentCharts.map((chart, index) => ({
          position: index,
          source: chart.query_id ? {
            // 기존 쿼리에서 생성된 차트는 참조 방식
            type: "query_reference",
            query_id: chart.query_id,
            title: chart.title || chart.config?.options?.plugins?.title?.text || `차트 ${index + 1}`,
            custom_options: {}
          } : {
            // 직접 추가된 차트는 인라인 방식
            type: "inline_data",
            chart_data: chart
          }
        }))
      }
    };

    const url = getApiUrl('/presets');
    console.log('프리셋 저장 URL:', url); // 디버깅용
    console.log('프리셋 저장 데이터:', presetData); // 디버깅용

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(presetData)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('프리셋 저장 실패:', response.status, response.statusText, errorText);
      throw new Error('프리셋 저장 실패');
    }

    await loadPresets(); // 목록 새로고침
  }, [username, apiUrl, activeTab, loadPresets]);

  const loadPreset = useCallback(async (presetId) => {
    if (!username) return;

    const url = getApiUrl(`/presets/${presetId}`);
    console.log('프리셋 로드 URL:', url); // 디버깅용
    
    const response = await fetch(url);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('프리셋 로드 실패:', response.status, response.statusText, errorText);
      throw new Error('프리셋 로드 실패');
    }

    const data = await response.json();
    console.log('🔍 프리셋 응답 데이터:', data);
    console.log('🔍 차트 개수:', data.charts?.length);
    
    if (data.charts) {
      data.charts.forEach((item, index) => {
        console.log(`🔍 차트 ${index}:`, item.chart_data);
        console.log(`🔍 차트 ${index} config 존재:`, !!item.chart_data?.config);
      });
    }
    
    return data.charts.map(item => item.chart_data);
  }, [username, apiUrl]);

  const deletePreset = useCallback(async (presetId) => {
    if (!username) return;

    const url = getApiUrl(`/presets/${presetId}`);
    console.log('프리셋 삭제 URL:', url); // 디버깅용
    
    const response = await fetch(url, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('프리셋 삭제 실패:', response.status, response.statusText, errorText);
      throw new Error('프리셋 삭제 실패');
    }

    await loadPresets(); // 목록 새로고침
  }, [username, apiUrl, loadPresets]);

  useEffect(() => {
    loadPresets();
  }, [loadPresets]);

  return {
    presets,
    loading,
    savePreset,
    loadPreset,
    deletePreset,
    refreshPresets: loadPresets
  };
};

// 메인 앱 컴포넌트 - username과 apiUrl을 props로 받음
function App({ username, apiUrl }) {
  // props로 받은 값들 사용, 없으면 기본값
  const API_URL = apiUrl || 'http://localhost:8000';
  const isUserMode = !!username;  // 사용자 모드인지 확인
  
  const [activeTab, setActiveTab] = useState('tab1');
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showLLM, setShowLLM] = useState(false);
  const [dataModal, setDataModal] = useState(null);

  // 드래그 앤 드롭 상태 관리
  const [dragState, setDragState] = useState({
    dragging: null,
    dragOver: null,
    dragOverType: null
  });

  // 차트 교체 모달 상태
  const [replaceModal, setReplaceModal] = useState({
    isOpen: false,
    sourceChart: null,
    targetIndex: null
  });

  // 프리셋 관련 상태
  const [showSavePresetModal, setShowSavePresetModal] = useState(false);
  
  // 프리셋 관리 훅 사용
  const {
    presets,
    loading: presetsLoading,
    savePreset,
    loadPreset,
    deletePreset
  } = usePresets(username, API_URL, activeTab);

  const tabs = [
    { id: 'tab1', name: '실적 데이터' },
    { id: 'tab2', name: '제품 정보' },
    { id: 'tab3', name: '고객 분석' }
  ];

  // 탭 데이터 로드
  const loadTabData = async (tabId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/tabs/${tabId}/data`);
      if (!response.ok) throw new Error('데이터 로드 실패');
      
      const data = await response.json();
      setCharts(data.charts || []);
    } catch (err) {
      setError(err.message);
      setCharts([]);
    } finally {
      setLoading(false);
    }
  };

  // 탭 변경 시 데이터 로드
  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab]);
  
  // 초기 로드 시 모든 탭 데이터 미리 로드 (선택사항)
  useEffect(() => {
    if (isUserMode) {
      // 사용자 모드에서는 모든 탭 데이터를 미리 로드
      tabs.forEach(tab => {
        fetch(`${API_URL}/api/tabs/${tab.id}/data`)
          .then(res => res.json())
          .then(data => {
            console.log(`${tab.id} 데이터 프리로드 완료`);
          })
          .catch(err => console.error(`${tab.id} 프리로드 실패:`, err));
      });
    }
  }, [isUserMode, API_URL]);

  // + 버튼으로 그리드에 추가 (기존 방식 유지)
  const handleAddToGrid = useCallback((newChart) => {
    const chartWithId = {
      ...newChart,
      id: `custom_${Date.now()}`
    };
    setCharts(prev => [...prev, chartWithId]);
    
    // 차트 저장 로직 제거 (불필요한 API 호출 방지)
    // 프리셋으로 저장하는 것으로 충분함
  }, []);

  // 드래그 시작
  const handleDragStart = useCallback((index) => {
    setDragState(prev => ({ ...prev, dragging: index }));
  }, []);

  // 드래그 종료
  const handleDragEnd = useCallback(() => {
    setDragState({ dragging: null, dragOver: null, dragOverType: null });
  }, []);

  // 드래그 오버
  const handleDragOver = useCallback((index) => {
    setDragState(prev => ({ 
      ...prev, 
      dragOver: index,
      dragOverType: prev.dragging !== null ? DRAG_TYPES.REORDER : DRAG_TYPES.REPLACE
    }));
  }, []);

  // 드래그 리브
  const handleDragLeave = useCallback(() => {
    setDragState(prev => ({ ...prev, dragOver: null, dragOverType: null }));
  }, []);

  // 드롭 처리
  const handleDrop = useCallback((targetIndex, draggedData) => {
    const { chart: draggedChart, index: sourceIndex, type, source } = draggedData;

    if (type === DRAG_TYPES.REORDER && sourceIndex !== undefined && source === 'grid') {
      // 그리드 내 위치 변경
      setCharts(prev => {
        const newCharts = [...prev];
        const [removed] = newCharts.splice(sourceIndex, 1);
        newCharts.splice(targetIndex, 0, removed);
        return newCharts;
      });
    } else if (type === DRAG_TYPES.REPLACE && source === 'new') {
      // 새 차트로 교체 - 확인 모달 표시
      setReplaceModal({
        isOpen: true,
        sourceChart: draggedChart,
        targetIndex
      });
    }

    handleDragEnd();
  }, [handleDragEnd]);

  // 차트 교체 확인
  const handleReplaceConfirm = useCallback(() => {
    const { sourceChart, targetIndex } = replaceModal;
    
    setCharts(prev => prev.map((chart, index) => 
      index === targetIndex 
        ? { ...sourceChart, id: chart.id } // ID는 유지하고 내용만 교체
        : chart
    ));
    
    setReplaceModal({ isOpen: false, sourceChart: null, targetIndex: null });
  }, [replaceModal]);

  // 프리셋 저장 처리
  const handleSavePreset = useCallback(async (name, description) => {
    if (charts.length === 0) {
      // alert 대신 에러 상태로 처리
      setError('저장할 차트가 없습니다.');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      await savePreset(name, description, charts);
      // alert 대신 성공 메시지 처리 (추후 toast 컴포넌트로 개선 가능)
      console.log('프리셋이 성공적으로 저장되었습니다.');
    } catch (error) {
      setError('프리셋 저장에 실패했습니다.');
      setTimeout(() => setError(null), 3000);
    }
  }, [charts, savePreset]);

  // 프리셋 로드 처리
  const handleLoadPreset = useCallback(async (presetId) => {
    try {
      const loadedCharts = await loadPreset(presetId);
      // 로드된 차트에 ID가 없는 경우 생성
      const chartsWithId = loadedCharts.map((chart, index) => ({
        ...chart,
        id: chart.id || `preset_chart_${Date.now()}_${index}`
      }));
      setCharts(chartsWithId);
    } catch (error) {
      console.error('프리셋 로드 실패:', error);
      setError('프리셋 로드에 실패했습니다.');
      setTimeout(() => setError(null), 3000);
    }
  }, [loadPreset]);

  // 차트 추가 이벤트 리스너
  useEffect(() => {
    const handleAddChart = (e) => {
      handleAddToGrid(e.detail);
    };

    const handleShowData = (e) => {
      setDataModal({ data: e.detail });
    };

    window.addEventListener('addChartToGrid', handleAddChart);
    window.addEventListener('showDataTable', handleShowData);

    return () => {
      window.removeEventListener('addChartToGrid', handleAddChart);
      window.removeEventListener('showDataTable', handleShowData);
    };
  }, [handleAddToGrid]);

  const removeChart = (chartId) => {
    setCharts(prev => prev.filter(c => c.id !== chartId));
  };

  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold">
              LLM 기반 차트 시각화 시스템
              {isUserMode && <span className="text-sm text-gray-500 ml-2">({username})</span>}
            </h1>
            <div className="flex items-center gap-4">
              {isUserMode && (
                <button
                  onClick={() => navigate(`/history/${username}`, '_blank')}
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  📜 히스토리
                </button>
              )}
              <button
                onClick={() => setShowLLM(!showLLM)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                <MessageCircle size={20} />
                LLM 분석
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 탭 네비게이션 */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* 프리셋 컨트롤 바 */}
      {isUserMode && (
        <div className="bg-gray-50 border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <PresetSelector
                  presets={presets}
                  loading={presetsLoading}
                  onLoad={handleLoadPreset}
                  onSave={() => setShowSavePresetModal(true)}
                  onDelete={deletePreset}
                />
              </div>
              <div className="text-sm text-gray-600">
                현재 {charts.length}개 차트
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="animate-spin" size={48} />
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2">
            <AlertCircle size={20} />
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* 사용법 안내 */}
            <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-800 mb-2">💡 차트 조작 방법</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <div>➕ <strong>추가:</strong> LLM 채팅에서 생성된 차트 위에 마우스를 올려 + 버튼 클릭</div>
                <div>📍 <strong>위치 변경:</strong> 차트를 드래그하여 다른 위치로 이동</div>
                <div>🔄 <strong>내용 교체:</strong> LLM 채팅의 차트를 기존 차트로 드래그</div>
                {isUserMode && (
                  <div>💾 <strong>프리셋 저장:</strong> 현재 상태를 프리셋으로 저장하고 나중에 불러오기</div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {charts.map((chart, index) => {
                // 방어 코드: chart나 chart.id가 없는 경우 처리
                if (!chart) {
                  console.warn(`차트 데이터가 없습니다 (index: ${index})`);
                  return null;
                }
                
                // ID가 없는 경우 임시 ID 생성
                const chartId = chart.id || `temp_chart_${index}`;
                const chartWithId = { ...chart, id: chartId };
                
                return (
                  <div key={chartId} className="h-80">
                    <ChartComponent
                      chartData={chartWithId}
                      index={index}
                      onShowData={(data) => setDataModal({ data })}
                      onRemove={chartId && chartId.startsWith('custom_') ? () => removeChart(chartId) : null}
                      // 드래그 앤 드롭 props
                      isGridChart={true}
                      isDragging={dragState.dragging === index}
                      isDragOver={dragState.dragOver === index}
                      dragOverType={dragState.dragOverType}
                      onDragStart={handleDragStart}
                      onDragEnd={handleDragEnd}
                      onDragOver={handleDragOver}
                      onDragLeave={handleDragLeave}
                      onDrop={handleDrop}
                    />
                  </div>
                );
              })}
            </div>
          </>
        )}
      </main>

      {/* LLM 채팅 패널 - username과 apiUrl 전달 */}
      <LLMChatPanel
        isOpen={showLLM}
        onClose={() => setShowLLM(false)}
        currentTab={activeTab}
        username={username}
        apiUrl={API_URL}
      />

      {/* 프리셋 저장 모달 */}
      <SavePresetModal
        isOpen={showSavePresetModal}
        onSave={handleSavePreset}
        onClose={() => setShowSavePresetModal(false)}
      />

      {/* 차트 교체 확인 모달 */}
      <ReplaceConfirmModal
        isOpen={replaceModal.isOpen}
        sourceChart={replaceModal.sourceChart}
        targetChart={charts[replaceModal.targetIndex]}
        onConfirm={handleReplaceConfirm}
        onCancel={() => setReplaceModal({ isOpen: false, sourceChart: null, targetIndex: null })}
      />

      {/* 데이터 테이블 모달 */}
      {dataModal && (
        <DataTableModal
          data={dataModal.data}
          columns={dataModal.columns}
          onClose={() => setDataModal(null)}
        />
      )}
    </div>
  );
}

export default App;
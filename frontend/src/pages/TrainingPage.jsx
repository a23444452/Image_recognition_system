import { useState } from 'react';
import TrainingForm from '../components/TrainingForm';
import TrainingMonitor from '../components/TrainingMonitor';

/**
 * 訓練頁面
 * 整合訓練配置表單與監控頁面
 */
export default function TrainingPage() {
  const [view, setView] = useState('form'); // 'form' | 'monitor' | 'list'
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/training/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '創建訓練任務失敗');
      }

      const data = await response.json();
      setCurrentTaskId(data.id);
      setView('monitor');
    } catch (err) {
      console.error('Failed to start training:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (confirm('確定要取消嗎？所有填寫的資料將會遺失。')) {
      setView('form');
      setCurrentTaskId(null);
      setError(null);
    }
  };

  const handleCloseMonitor = () => {
    setView('form');
    setCurrentTaskId(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      {/* 載入覆蓋層 */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
            <p className="text-lg font-medium text-gray-700">創建訓練任務中...</p>
          </div>
        </div>
      )}

      {/* 錯誤訊息 */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center justify-between">
            <p className="text-red-800 font-medium">❌ {error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 條件渲染 */}
      {view === 'form' && (
        <TrainingForm onSubmit={handleSubmit} onCancel={handleCancel} />
      )}

      {view === 'monitor' && currentTaskId && (
        <TrainingMonitor taskId={currentTaskId} onClose={handleCloseMonitor} />
      )}
    </div>
  );
}

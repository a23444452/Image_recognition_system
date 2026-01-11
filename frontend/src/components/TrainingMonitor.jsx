import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * 訓練監控頁面
 * 即時顯示訓練進度與指標
 */
export default function TrainingMonitor({ taskId, onClose }) {
  const [status, setStatus] = useState('connecting');
  const [progress, setProgress] = useState(0);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [totalEpochs, setTotalEpochs] = useState(0);
  const [metrics, setMetrics] = useState({
    loss: null,
    map: null,
  });
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const logsEndRef = useRef(null);

  // 自動滾動到日誌底部
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  // WebSocket 連線
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/training/${taskId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      addLog('✅ WebSocket 連線成功');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case 'connected':
            addLog(message.message);
            break;

          case 'progress':
            handleProgressUpdate(message.data);
            break;

          case 'finished':
            handleTrainingFinished(message.data);
            break;

          case 'error':
            setError(message.message);
            addLog(`❌ 錯誤: ${message.message}`);
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket 連線錯誤');
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus('disconnected');
      addLog('⚠️ WebSocket 連線已關閉');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [taskId]);

  const handleProgressUpdate = (data) => {
    setStatus(data.status);
    setProgress(data.progress);
    setCurrentEpoch(data.current_epoch);
    setTotalEpochs(data.total_epochs);
    setMetrics({
      loss: data.current_loss,
      map: data.current_map,
    });

    // 更新歷史數據
    if (data.current_epoch > 0) {
      setHistory((prev) => {
        const newData = {
          epoch: data.current_epoch,
          loss: data.current_loss || 0,
          map: data.current_map || 0,
        };

        // 檢查是否已存在該 epoch
        const existingIndex = prev.findIndex((item) => item.epoch === data.current_epoch);
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = newData;
          return updated;
        }

        return [...prev, newData];
      });

      addLog(
        `📊 Epoch ${data.current_epoch}/${data.total_epochs} - Loss: ${data.current_loss?.toFixed(4) || 'N/A'}, mAP: ${data.current_map?.toFixed(4) || 'N/A'}`
      );
    }
  };

  const handleTrainingFinished = (data) => {
    setStatus(data.status);

    if (data.status === 'completed') {
      addLog('🎉 訓練完成！');
      addLog(`📁 模型路徑: ${data.model_path}`);
      addLog(`📁 結果目錄: ${data.save_dir}`);
    } else if (data.status === 'failed') {
      setError(data.error_message);
      addLog(`❌ 訓練失敗: ${data.error_message}`);
    } else if (data.status === 'stopped') {
      addLog('⏸️ 訓練已停止');
    }
  };

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString('zh-TW');
    setLogs((prev) => [...prev, { time: timestamp, message }]);
  };

  const handleStop = async () => {
    if (!confirm('確定要停止訓練嗎？')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/v1/training/${taskId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        addLog('⏹️ 已發送停止請求');
      } else {
        const data = await response.json();
        setError(data.detail || '停止失敗');
      }
    } catch (err) {
      console.error('Failed to stop training:', err);
      setError('停止訓練失敗');
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'running':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'stopped':
        return 'bg-gray-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connecting':
        return '連線中...';
      case 'connected':
        return '已連線';
      case 'pending':
        return '等待中';
      case 'running':
        return '訓練中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失敗';
      case 'stopped':
        return '已停止';
      case 'disconnected':
        return '已斷線';
      case 'error':
        return '錯誤';
      default:
        return '未知';
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* 標題列 */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">訓練監控</h1>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
            <span className="text-sm font-medium text-gray-700">{getStatusText()}</span>
          </div>
          {(status === 'pending' || status === 'running') && (
            <button
              onClick={handleStop}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              停止訓練
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            關閉
          </button>
        </div>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 font-medium">❌ {error}</p>
        </div>
      )}

      {/* 進度卡片 */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">訓練進度</h2>

        {/* 進度條 */}
        <div className="mb-6">
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Epoch {currentEpoch} / {totalEpochs}
            </span>
            <span className="text-sm font-medium text-gray-700">{progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* 指標卡片 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">當前 Loss</p>
            <p className="text-2xl font-bold text-blue-700">
              {metrics.loss !== null ? metrics.loss.toFixed(4) : 'N/A'}
            </p>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">當前 mAP</p>
            <p className="text-2xl font-bold text-green-700">
              {metrics.map !== null ? metrics.map.toFixed(4) : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* 訓練圖表 */}
      {history.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">訓練指標</h2>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="epoch"
                label={{ value: 'Epoch', position: 'insideBottom', offset: -5 }}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="loss"
                stroke="#3B82F6"
                name="Loss"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="map"
                stroke="#10B981"
                name="mAP"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 訓練日誌 */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">訓練日誌</h2>

        <div className="bg-gray-900 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
          {logs.map((log, index) => (
            <div key={index} className="text-gray-300 mb-1">
              <span className="text-gray-500">[{log.time}]</span> {log.message}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}

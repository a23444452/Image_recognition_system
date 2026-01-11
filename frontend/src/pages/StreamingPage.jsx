import { useState, useEffect, useRef } from 'react';

/**
 * 串流偵測頁面
 * 即時攝影機串流與 YOLO 物件偵測
 */
export default function StreamingPage() {
  // 狀態管理
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [config, setConfig] = useState({
    camera_id: 0,
    conf_threshold: 0.25,
    iou_threshold: 0.45,
    use_gray: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detectionCount, setDetectionCount] = useState(0);
  const [fps, setFps] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [detections, setDetections] = useState([]);

  // WebSocket 引用
  const wsRef = useRef(null);
  const fpsCounterRef = useRef({ frames: 0, lastTime: Date.now() });

  // 載入可用模型列表
  useEffect(() => {
    fetchModels();
    fetchStatus();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/models');
      if (response.ok) {
        const data = await response.json();
        setModels(data);
        // 預設選擇 active 模型
        const activeModel = data.find((m) => m.is_active);
        if (activeModel) {
          setSelectedModel(activeModel.model_path);
        }
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/streaming/status');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        setIsStreaming(data.is_streaming);
        setConfig({
          camera_id: data.camera_id,
          conf_threshold: data.conf_threshold,
          iou_threshold: data.iou_threshold,
          use_gray: data.use_gray,
        });
      }
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  // 啟動串流
  const handleStart = async () => {
    if (!selectedModel) {
      setError('請選擇模型');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/streaming/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          camera_id: config.camera_id,
          model_path: selectedModel,
          conf_threshold: config.conf_threshold,
          iou_threshold: config.iou_threshold,
          use_gray: config.use_gray,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '啟動串流失敗');
      }

      const data = await response.json();
      setStatus(data);
      setIsStreaming(true);

      // 連接 WebSocket
      connectWebSocket();
    } catch (err) {
      console.error('Failed to start streaming:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 停止串流
  const handleStop = async () => {
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/streaming/stop', {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '停止串流失敗');
      }

      setIsStreaming(false);
      setCurrentFrame(null);
      setDetections([]);
      setDetectionCount(0);
      setFps(0);

      // 關閉 WebSocket
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    } catch (err) {
      console.error('Failed to stop streaming:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 連接 WebSocket
  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/streaming/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'frame') {
        const frameData = message.data;
        setCurrentFrame(frameData.frame);
        setDetections(frameData.detections || []);
        setDetectionCount(frameData.detection_count || 0);

        // 計算 FPS
        const counter = fpsCounterRef.current;
        counter.frames++;
        const now = Date.now();
        const elapsed = (now - counter.lastTime) / 1000;

        if (elapsed >= 1.0) {
          setFps(Math.round(counter.frames / elapsed));
          counter.frames = 0;
          counter.lastTime = now;
        }
      } else if (message.type === 'error') {
        setError(message.message);
      } else if (message.type === 'stopped') {
        setIsStreaming(false);
        setCurrentFrame(null);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket 連線錯誤');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    wsRef.current = ws;
  };

  // 更新配置
  const handleConfigUpdate = async (newConfig) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/streaming/config', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newConfig),
      });

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to update config:', err);
    }
  };

  // 配置變更處理
  const handleConfidenceChange = (value) => {
    const newConfig = { ...config, conf_threshold: value };
    setConfig(newConfig);
    if (isStreaming) {
      handleConfigUpdate({ conf_threshold: value });
    }
  };

  const handleIouChange = (value) => {
    const newConfig = { ...config, iou_threshold: value };
    setConfig(newConfig);
    if (isStreaming) {
      handleConfigUpdate({ iou_threshold: value });
    }
  };

  const handleGrayToggle = () => {
    const newConfig = { ...config, use_gray: !config.use_gray };
    setConfig(newConfig);
    if (isStreaming) {
      handleConfigUpdate({ use_gray: !config.use_gray });
    }
  };

  // 清理
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">📹 即時串流偵測</h1>

        {/* 錯誤訊息 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
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

        <div className="grid lg:grid-cols-3 gap-6">
          {/* 左側控制面板 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 模型選擇 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">模型配置</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    選擇模型
                  </label>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    disabled={isStreaming}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  >
                    <option value="">請選擇模型</option>
                    {models.map((model) => (
                      <option key={model.id} value={model.model_path}>
                        {model.name} (v{model.version})
                        {model.is_active && ' ⭐'}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    攝影機 ID
                  </label>
                  <input
                    type="number"
                    value={config.camera_id}
                    onChange={(e) =>
                      setConfig({ ...config, camera_id: parseInt(e.target.value) })
                    }
                    disabled={isStreaming}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  />
                </div>
              </div>
            </div>

            {/* 偵測配置 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">偵測配置</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    信心度閾值: {config.conf_threshold.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.conf_threshold}
                    onChange={(e) => handleConfidenceChange(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IOU 閾值: {config.iou_threshold.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={config.iou_threshold}
                    onChange={(e) => handleIouChange(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="use_gray"
                    checked={config.use_gray}
                    onChange={handleGrayToggle}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="use_gray" className="ml-2 text-sm text-gray-700">
                    使用灰階模式
                  </label>
                </div>
              </div>
            </div>

            {/* 控制按鈕 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">控制</h2>

              <div className="space-y-3">
                {!isStreaming ? (
                  <button
                    onClick={handleStart}
                    disabled={loading || !selectedModel}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                  >
                    {loading ? '啟動中...' : '▶ 開始串流'}
                  </button>
                ) : (
                  <button
                    onClick={handleStop}
                    disabled={loading}
                    className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-300 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                  >
                    {loading ? '停止中...' : '⏹ 停止串流'}
                  </button>
                )}
              </div>
            </div>

            {/* 統計資訊 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">統計</h2>

              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-gray-700">FPS</span>
                  <span className="font-semibold text-gray-900">{fps}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-gray-700">偵測數量</span>
                  <span className="font-semibold text-gray-900">{detectionCount}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="text-gray-700">狀態</span>
                  <span
                    className={`font-semibold ${
                      isStreaming ? 'text-green-600' : 'text-gray-500'
                    }`}
                  >
                    {isStreaming ? '🟢 串流中' : '🔴 已停止'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 右側畫面顯示 */}
          <div className="lg:col-span-2 space-y-6">
            {/* 影像顯示 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">即時畫面</h2>

              <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center">
                {currentFrame ? (
                  <img
                    src={currentFrame}
                    alt="Streaming frame"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="text-center text-gray-400">
                    {isStreaming ? (
                      <div className="space-y-3">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
                        <p>載入畫面中...</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="text-5xl">📹</div>
                        <p>點擊「開始串流」以顯示畫面</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* 偵測結果 */}
            {detections.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">
                  偵測結果 ({detections.length})
                </h2>

                <div className="max-h-96 overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
                          類別
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
                          信心度
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">
                          位置
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {detections.map((detection, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {detection.class_name}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {(detection.confidence * 100).toFixed(1)}%
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-600 font-mono text-xs">
                            ({detection.bbox.x1.toFixed(0)}, {detection.bbox.y1.toFixed(0)}) →
                            ({detection.bbox.x2.toFixed(0)}, {detection.bbox.y2.toFixed(0)})
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

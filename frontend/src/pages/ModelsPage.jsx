import { useState, useEffect } from 'react';

/**
 * 模型管理頁面
 */
export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterVersion, setFilterVersion] = useState('all');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showCompare, setShowCompare] = useState(false);
  const [selectedModels, setSelectedModels] = useState([]);

  useEffect(() => {
    fetchData();
  }, [filterVersion]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 取得模型列表
      const params = new URLSearchParams();
      if (filterVersion !== 'all') {
        params.append('yolo_version', filterVersion);
      }

      const modelsResponse = await fetch(
        `http://localhost:8000/api/v1/models?${params}`
      );

      if (!modelsResponse.ok) {
        throw new Error('無法取得模型列表');
      }

      const modelsData = await modelsResponse.json();
      setModels(modelsData);

      // 取得統計資訊
      const statsResponse = await fetch(
        'http://localhost:8000/api/v1/models/statistics'
      );

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatistics(statsData);
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (modelId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/models/${modelId}/activate`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('啟用模型失敗');
      }

      fetchData();
    } catch (err) {
      console.error('Failed to activate model:', err);
      setError(err.message);
    }
  };

  const handleDelete = async (modelId) => {
    if (!confirm('確定要刪除此模型嗎？')) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/models/${modelId}?delete_file=false`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error('刪除模型失敗');
      }

      fetchData();
    } catch (err) {
      console.error('Failed to delete model:', err);
      setError(err.message);
    }
  };

  const handleSelectModel = (modelId) => {
    setSelectedModels((prev) => {
      if (prev.includes(modelId)) {
        return prev.filter((id) => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 標題列 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">模型管理</h1>
            <p className="text-gray-600 mt-2">管理訓練完成的 YOLO 模型</p>
          </div>

          <div className="flex space-x-3">
            {selectedModels.length >= 2 && (
              <button
                onClick={() => setShowCompare(true)}
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                比較模型 ({selectedModels.length})
              </button>
            )}
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              + 註冊模型
            </button>
          </div>
        </div>

        {/* 統計卡片 */}
        {statistics && (
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">總模型數</p>
              <p className="text-3xl font-bold text-gray-800">{statistics.total}</p>
            </div>
            <div className="bg-blue-50 rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">YOLOv5</p>
              <p className="text-3xl font-bold text-blue-700">
                {statistics.by_version.v5}
              </p>
            </div>
            <div className="bg-green-50 rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">YOLOv8</p>
              <p className="text-3xl font-bold text-green-700">
                {statistics.by_version.v8}
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-2">YOLOv11</p>
              <p className="text-3xl font-bold text-purple-700">
                {statistics.by_version.v11}
              </p>
            </div>
          </div>
        )}

        {/* 過濾器 */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">過濾版本:</span>
            <div className="flex space-x-2">
              {['all', 'v5', 'v8', 'v11'].map((version) => (
                <button
                  key={version}
                  onClick={() => setFilterVersion(version)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filterVersion === version
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {version === 'all' ? '全部' : version.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 錯誤訊息 */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 font-medium">❌ {error}</p>
          </div>
        )}

        {/* 載入中 */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
          </div>
        )}

        {/* 模型列表 */}
        {!loading && models.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">尚無模型</h3>
            <p className="text-gray-500 mb-6">註冊第一個訓練完成的模型</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              註冊模型
            </button>
          </div>
        )}

        {!loading && models.length > 0 && (
          <div className="space-y-4">
            {models.map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                isSelected={selectedModels.includes(model.id)}
                onSelect={handleSelectModel}
                onActivate={handleActivate}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* 創建表單 Modal */}
        {showCreateForm && (
          <CreateModelModal
            onClose={() => setShowCreateForm(false)}
            onSuccess={() => {
              setShowCreateForm(false);
              fetchData();
            }}
          />
        )}

        {/* 模型比較 Modal */}
        {showCompare && (
          <CompareModelsModal
            modelIds={selectedModels}
            onClose={() => setShowCompare(false)}
          />
        )}
      </div>
    </div>
  );
}

/**
 * 模型卡片組件
 */
function ModelCard({ model, isSelected, onSelect, onActivate, onDelete }) {
  const metrics = model.metrics || {};
  const fileSizeMB = model.file_size
    ? (model.file_size / 1024 / 1024).toFixed(2)
    : 'N/A';

  return (
    <div
      className={`bg-white rounded-lg shadow-md hover:shadow-lg transition-all p-6 ${
        isSelected ? 'ring-2 ring-blue-500' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        {/* 左側：基本資訊 */}
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onSelect(model.id)}
              className="w-5 h-5 text-blue-600"
            />
            <h3 className="text-xl font-semibold text-gray-800">{model.name}</h3>
            {model.is_active && (
              <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                ✓ 啟用中
              </span>
            )}
            <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
              {model.yolo_version.toUpperCase()}
            </span>
          </div>

          {model.description && (
            <p className="text-sm text-gray-600 mb-4">{model.description}</p>
          )}

          <div className="flex items-center space-x-6 text-sm text-gray-600">
            <span>檔案大小: {fileSizeMB} MB</span>
            {model.training_task_id && (
              <span>訓練任務: {model.training_task_id.slice(0, 8)}...</span>
            )}
          </div>
        </div>

        {/* 右側：效能指標 */}
        <div className="grid grid-cols-2 gap-3 ml-6">
          <div className="bg-blue-50 p-3 rounded-lg text-center min-w-[100px]">
            <p className="text-xs text-gray-600 mb-1">mAP@0.5</p>
            <p className="text-lg font-bold text-blue-700">
              {metrics.map50 !== null ? (metrics.map50 * 100).toFixed(1) + '%' : 'N/A'}
            </p>
          </div>

          <div className="bg-green-50 p-3 rounded-lg text-center min-w-[100px]">
            <p className="text-xs text-gray-600 mb-1">mAP@0.5:0.95</p>
            <p className="text-lg font-bold text-green-700">
              {metrics.map50_95 !== null
                ? (metrics.map50_95 * 100).toFixed(1) + '%'
                : 'N/A'}
            </p>
          </div>

          <div className="bg-purple-50 p-3 rounded-lg text-center min-w-[100px]">
            <p className="text-xs text-gray-600 mb-1">Precision</p>
            <p className="text-lg font-bold text-purple-700">
              {metrics.precision !== null
                ? (metrics.precision * 100).toFixed(1) + '%'
                : 'N/A'}
            </p>
          </div>

          <div className="bg-orange-50 p-3 rounded-lg text-center min-w-[100px]">
            <p className="text-xs text-gray-600 mb-1">Recall</p>
            <p className="text-lg font-bold text-orange-700">
              {metrics.recall !== null
                ? (metrics.recall * 100).toFixed(1) + '%'
                : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* 操作按鈕 */}
      <div className="flex space-x-2 mt-4 pt-4 border-t">
        {!model.is_active && (
          <button
            onClick={() => onActivate(model.id)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
          >
            啟用
          </button>
        )}
        <button
          onClick={() => onDelete(model.id)}
          className="px-4 py-2 text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
        >
          刪除
        </button>
      </div>
    </div>
  );
}

/**
 * 創建模型 Modal
 */
function CreateModelModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    yolo_version: 'v11',
    file_path: '',
    description: '',
    training_task_id: '',
    map50: '',
    map50_95: '',
    precision: '',
    recall: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showFileBrowser, setShowFileBrowser] = useState(false);
  const [availableFiles, setAvailableFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [inspecting, setInspecting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBrowseFiles = async () => {
    setShowFileBrowser(true);
    setLoadingFiles(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/models/scan-files');

      if (!response.ok) {
        throw new Error('掃描模型檔案失敗');
      }

      const data = await response.json();
      setAvailableFiles(data.files || []);
    } catch (err) {
      console.error('Failed to scan model files:', err);
      setError(err.message);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleSelectFile = async (file) => {
    setInspecting(true);
    setError(null);

    try {
      // 檢查模型檔案，獲取指標
      const response = await fetch('http://localhost:8000/api/v1/models/inspect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_path: file.file_path }),
      });

      if (!response.ok) {
        throw new Error('讀取模型資訊失敗');
      }

      const modelInfo = await response.json();

      // 自動填充表單
      setFormData((prev) => ({
        ...prev,
        file_path: modelInfo.file_path,
        yolo_version: modelInfo.yolo_version || prev.yolo_version,
        map50: modelInfo.metrics.map50 || '',
        map50_95: modelInfo.metrics.map50_95 || '',
        precision: modelInfo.metrics.precision || '',
        recall: modelInfo.metrics.recall || '',
        // 自動生成模型名稱
        name: prev.name || modelInfo.file_name.replace('.pt', ''),
      }));

      setShowFileBrowser(false);
    } catch (err) {
      console.error('Failed to inspect model file:', err);
      setError(err.message);
    } finally {
      setInspecting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // 轉換數值
      const payload = {
        ...formData,
        map50: formData.map50 ? parseFloat(formData.map50) : null,
        map50_95: formData.map50_95 ? parseFloat(formData.map50_95) : null,
        precision: formData.precision ? parseFloat(formData.precision) : null,
        recall: formData.recall ? parseFloat(formData.recall) : null,
        training_task_id: formData.training_task_id || null,
      };

      const response = await fetch('http://localhost:8000/api/v1/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '註冊模型失敗');
      }

      onSuccess();
    } catch (err) {
      console.error('Failed to create model:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">註冊模型</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-medium">❌ {error}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型名稱 *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YOLO 版本 *
              </label>
              <select
                name="yolo_version"
                value={formData.yolo_version}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="v5">YOLOv5</option>
                <option value="v8">YOLOv8</option>
                <option value="v11">YOLOv11</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              模型檔案路徑 *
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                name="file_path"
                value={formData.file_path}
                onChange={handleChange}
                required
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="/path/to/model.pt"
              />
              <button
                type="button"
                onClick={handleBrowseFiles}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                瀏覽檔案
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">描述</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="2"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              訓練任務 ID（可選）
            </label>
            <input
              type="text"
              name="training_task_id"
              value={formData.training_task_id}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                mAP@0.5
              </label>
              <input
                type="number"
                name="map50"
                value={formData.map50}
                onChange={handleChange}
                step="0.001"
                min="0"
                max="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                mAP@0.5:0.95
              </label>
              <input
                type="number"
                name="map50_95"
                value={formData.map50_95}
                onChange={handleChange}
                step="0.001"
                min="0"
                max="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Precision
              </label>
              <input
                type="number"
                name="precision"
                value={formData.precision}
                onChange={handleChange}
                step="0.001"
                min="0"
                max="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Recall</label>
              <input
                type="number"
                name="recall"
                value={formData.recall}
                onChange={handleChange}
                step="0.001"
                min="0"
                max="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? '註冊中...' : '註冊'}
            </button>
          </div>
        </form>

        {/* 檔案瀏覽器 Modal */}
        {showFileBrowser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-y-auto m-4">
              <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-white">
                <h3 className="text-lg font-semibold text-gray-800">選擇模型檔案</h3>
                <button
                  onClick={() => setShowFileBrowser(false)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="p-4">
                {loadingFiles && (
                  <div className="flex justify-center items-center py-10">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-4 border-blue-600"></div>
                  </div>
                )}

                {!loadingFiles && availableFiles.length === 0 && (
                  <div className="text-center py-10">
                    <p className="text-gray-600">找不到可用的模型檔案</p>
                    <p className="text-sm text-gray-500 mt-2">
                      請確認訓練完成並且模型檔案存在於正確的目錄
                    </p>
                  </div>
                )}

                {!loadingFiles && availableFiles.length > 0 && (
                  <div className="space-y-2">
                    {availableFiles.map((file, index) => (
                      <button
                        key={index}
                        onClick={() => handleSelectFile(file)}
                        disabled={inspecting}
                        className="w-full text-left p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <p className="font-medium text-gray-800">{file.file_name}</p>
                              {file.model_type === 'best' && (
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                                  最佳
                                </span>
                              )}
                              {file.model_type === 'last' && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                  最後
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-500 mt-1">
                              {file.directory}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              大小: {file.file_size_mb} MB
                            </p>
                          </div>
                          <div className="text-blue-600">
                            {inspecting ? '讀取中...' : '選擇'}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 模型比較 Modal
 */
function CompareModelsModal({ modelIds, onClose }) {
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchComparison();
  }, []);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/models/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_ids: modelIds }),
      });

      if (!response.ok) {
        throw new Error('比較模型失敗');
      }

      const data = await response.json();
      setComparison(data.models);
    } catch (err) {
      console.error('Failed to compare models:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">模型比較</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6">
          {loading && (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-medium">❌ {error}</p>
            </div>
          )}

          {!loading && comparison.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      模型名稱
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">
                      版本
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      檔案大小
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      mAP@0.5
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      mAP@0.5:0.95
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Precision
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      Recall
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-700">
                      狀態
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.map((model) => (
                    <tr key={model.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{model.name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                          {model.yolo_version.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.file_size_mb ? `${model.file_size_mb} MB` : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.metrics.map50 !== null
                          ? (model.metrics.map50 * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.metrics.map50_95 !== null
                          ? (model.metrics.map50_95 * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.metrics.precision !== null
                          ? (model.metrics.precision * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.metrics.recall !== null
                          ? (model.metrics.recall * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {model.is_active && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                            啟用中
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="flex justify-end p-6 border-t">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  );
}

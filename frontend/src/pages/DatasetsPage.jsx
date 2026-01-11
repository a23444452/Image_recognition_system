import { useState, useEffect } from 'react';

/**
 * 資料集管理頁面
 */
export default function DatasetsPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/datasets');

      if (!response.ok) {
        throw new Error('無法取得資料集列表');
      }

      const data = await response.json();
      setDatasets(data);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (datasetId) => {
    if (!confirm('確定要刪除此資料集嗎？')) {
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/datasets/${datasetId}?delete_files=false`,
        { method: 'DELETE' }
      );

      if (!response.ok) {
        throw new Error('刪除資料集失敗');
      }

      // 重新載入列表
      fetchDatasets();
    } catch (err) {
      console.error('Failed to delete dataset:', err);
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* 標題列 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">資料集管理</h1>
            <p className="text-gray-600 mt-2">管理 YOLO 訓練資料集</p>
          </div>

          <button
            onClick={() => setShowCreateForm(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            + 創建資料集
          </button>
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

        {/* 資料集列表 */}
        {!loading && datasets.length === 0 && (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📁</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">尚無資料集</h3>
            <p className="text-gray-500 mb-6">建立第一個資料集開始訓練</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              創建資料集
            </button>
          </div>
        )}

        {!loading && datasets.length > 0 && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {datasets.map((dataset) => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* 創建表單 Modal */}
        {showCreateForm && (
          <CreateDatasetModal
            onClose={() => setShowCreateForm(false)}
            onSuccess={() => {
              setShowCreateForm(false);
              fetchDatasets();
            }}
          />
        )}
      </div>
    </div>
  );
}

/**
 * 資料集卡片組件
 */
function DatasetCard({ dataset, onDelete }) {
  const stats = dataset.stats || {};

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
      {/* 標題 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-1">{dataset.name}</h3>
          {dataset.description && (
            <p className="text-sm text-gray-600">{dataset.description}</p>
          )}
        </div>
      </div>

      {/* 統計資訊 */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">總圖片數</p>
          <p className="text-xl font-bold text-blue-700">{stats.total_images || 0}</p>
        </div>

        <div className="bg-green-50 p-3 rounded-lg">
          <p className="text-xs text-gray-600 mb-1">類別數</p>
          <p className="text-xl font-bold text-green-700">{stats.num_classes || 0}</p>
        </div>
      </div>

      {/* 類別名稱 */}
      {stats.class_names && stats.class_names.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-600 mb-2">類別</p>
          <div className="flex flex-wrap gap-1">
            {stats.class_names.slice(0, 5).map((name, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
              >
                {name}
              </span>
            ))}
            {stats.class_names.length > 5 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                +{stats.class_names.length - 5}
              </span>
            )}
          </div>
        </div>
      )}

      {/* 操作按鈕 */}
      <div className="flex space-x-2 pt-4 border-t">
        <button
          onClick={() => onDelete(dataset.id)}
          className="flex-1 px-4 py-2 text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
        >
          刪除
        </button>
      </div>
    </div>
  );
}

/**
 * 創建資料集 Modal
 */
function CreateDatasetModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    source_folder: '',
    split_ratio: 0.8,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'split_ratio' ? parseFloat(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/datasets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '創建資料集失敗');
      }

      onSuccess();
    } catch (err) {
      console.error('Failed to create dataset:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* 標題 */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">創建資料集</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* 表單 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 font-medium">❌ {error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              資料集名稱 *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="例如：safety_helmet_dataset"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              描述
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="描述資料集用途與內容"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              原始資料夾路徑
            </label>
            <input
              type="text"
              name="source_folder"
              value={formData.source_folder}
              onChange={handleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="/path/to/raw/dataset"
            />
            <p className="mt-1 text-sm text-gray-500">
              包含圖片和標註檔的資料夾路徑
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              訓練集比例: {(formData.split_ratio * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              name="split_ratio"
              value={formData.split_ratio}
              onChange={handleChange}
              min="0.5"
              max="0.95"
              step="0.05"
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>50%</span>
              <span>95%</span>
            </div>
          </div>

          {/* 按鈕 */}
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
              {loading ? '創建中...' : '創建'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

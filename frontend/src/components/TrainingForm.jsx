import { useState, useEffect } from 'react';

/**
 * 訓練配置表單
 * 多步驟表單收集訓練參數
 */
export default function TrainingForm({ onSubmit, onCancel }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    // 基本配置
    project_name: 'yolo_project',
    model_name: 'training',
    yolo_version: 'v11',

    // 訓練參數
    epochs: 100,
    batch_size: 8,
    img_size: 640,

    // 資料集
    dataset_id: '',
    data_yaml: '',
    train_path: '',
    val_path: '',
    class_names: '',

    // 進階參數
    device: 'auto',
    workers: 4,
    optimizer: 'AdamW',
    patience: 20,
    lr0: 0.001,
    cosine_lr: true,

    // 資料增強
    augment: true,
    degrees: 10.0,
    flipLR: 0.5,
    mosaic: 1.0,
  });

  const [datasets, setDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [errors, setErrors] = useState({});

  // 載入資料集列表
  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    setLoadingDatasets(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/datasets');
      if (response.ok) {
        const data = await response.json();
        setDatasets(data);
      }
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
    } finally {
      setLoadingDatasets(false);
    }
  };

  const handleDatasetSelect = (datasetId) => {
    const selected = datasets.find(ds => ds.id === datasetId);
    if (selected) {
      const classNames = selected.stats?.class_names?.join(', ') || '';
      setFormData(prev => ({
        ...prev,
        dataset_id: datasetId,
        data_yaml: selected.yaml_path || '',
        train_path: selected.train_path || '',
        val_path: selected.val_path || '',
        class_names: classNames
      }));

      // 清除相關欄位的錯誤
      setErrors(prev => ({
        ...prev,
        dataset_id: null,
        data_yaml: null,
        class_names: null
      }));
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    // 如果是資料集選擇器，使用特殊處理
    if (name === 'dataset_id') {
      handleDatasetSelect(value);
      return;
    }

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // 清除該欄位的錯誤
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validateStep = (currentStep) => {
    const newErrors = {};

    if (currentStep === 1) {
      if (!formData.project_name.trim()) {
        newErrors.project_name = '專案名稱不可為空';
      }
      if (!formData.model_name.trim()) {
        newErrors.model_name = '模型名稱不可為空';
      }
    }

    if (currentStep === 2) {
      if (formData.epochs < 1 || formData.epochs > 1000) {
        newErrors.epochs = 'Epochs 必須在 1-1000 之間';
      }
      if (formData.batch_size < 1 || formData.batch_size > 128) {
        newErrors.batch_size = 'Batch Size 必須在 1-128 之間';
      }
      if (![320, 416, 512, 640, 800, 1024].includes(parseInt(formData.img_size))) {
        newErrors.img_size = '請選擇有效的圖片尺寸';
      }
    }

    if (currentStep === 3) {
      if (!formData.dataset_id.trim()) {
        newErrors.dataset_id = '請選擇資料集';
      }
      if (!formData.data_yaml.trim()) {
        newErrors.data_yaml = 'Data YAML 路徑不可為空';
      }
      // class_names 為可選欄位，因為訓練主要依賴 data.yaml
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(prev => Math.min(prev + 1, 4));
    }
  };

  const handlePrev = () => {
    setStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (validateStep(step)) {
      // 轉換數值型別
      const processedData = {
        ...formData,
        epochs: parseInt(formData.epochs),
        batch_size: parseInt(formData.batch_size),
        img_size: parseInt(formData.img_size),
        workers: parseInt(formData.workers),
        patience: parseInt(formData.patience),
        lr0: parseFloat(formData.lr0),
        degrees: parseFloat(formData.degrees),
        flipLR: parseFloat(formData.flipLR),
        mosaic: parseFloat(formData.mosaic),
      };

      onSubmit(processedData);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* 步驟指示器 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex-1 flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  s === step
                    ? 'bg-blue-600 text-white'
                    : s < step
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {s < step ? '✓' : s}
              </div>
              {s < 4 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    s < step ? 'bg-green-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={step >= 1 ? 'text-blue-600 font-medium' : 'text-gray-500'}>基本設定</span>
          <span className={step >= 2 ? 'text-blue-600 font-medium' : 'text-gray-500'}>訓練參數</span>
          <span className={step >= 3 ? 'text-blue-600 font-medium' : 'text-gray-500'}>資料集</span>
          <span className={step >= 4 ? 'text-blue-600 font-medium' : 'text-gray-500'}>進階選項</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: 基本設定 */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">基本設定</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                專案名稱 *
              </label>
              <input
                type="text"
                name="project_name"
                value={formData.project_name}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.project_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例如：safety_helmet_detection"
              />
              {errors.project_name && (
                <p className="mt-1 text-sm text-red-600">{errors.project_name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型名稱 *
              </label>
              <input
                type="text"
                name="model_name"
                value={formData.model_name}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.model_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="例如：helmet_v1"
              />
              {errors.model_name && (
                <p className="mt-1 text-sm text-red-600">{errors.model_name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YOLO 版本
              </label>
              <select
                name="yolo_version"
                value={formData.yolo_version}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="v5">YOLOv5</option>
                <option value="v8">YOLOv8</option>
                <option value="v11">YOLOv11 (推薦)</option>
              </select>
            </div>
          </div>
        )}

        {/* Step 2: 訓練參數 */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">訓練參數</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Epochs *
              </label>
              <input
                type="number"
                name="epochs"
                value={formData.epochs}
                onChange={handleChange}
                min="1"
                max="1000"
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.epochs ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.epochs && (
                <p className="mt-1 text-sm text-red-600">{errors.epochs}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">訓練回合數，建議 100-300</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Batch Size *
                </label>
                <input
                  type="number"
                  name="batch_size"
                  value={formData.batch_size}
                  onChange={handleChange}
                  min="1"
                  max="128"
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    errors.batch_size ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.batch_size && (
                  <p className="mt-1 text-sm text-red-600">{errors.batch_size}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Image Size
                </label>
                <select
                  name="img_size"
                  value={formData.img_size}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="320">320</option>
                  <option value="416">416</option>
                  <option value="512">512</option>
                  <option value="640">640 (推薦)</option>
                  <option value="800">800</option>
                  <option value="1024">1024</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Device
                </label>
                <select
                  name="device"
                  value={formData.device}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="auto">自動選擇</option>
                  <option value="cpu">CPU</option>
                  <option value="gpu">GPU (CUDA)</option>
                  <option value="mps">Apple Silicon (MPS)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workers
                </label>
                <input
                  type="number"
                  name="workers"
                  value={formData.workers}
                  onChange={handleChange}
                  min="0"
                  max="32"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: 資料集 */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">資料集配置</h2>

            {/* 資料集選擇器 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                選擇資料集 *
              </label>
              <select
                name="dataset_id"
                value={formData.dataset_id}
                onChange={handleChange}
                disabled={loadingDatasets}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.dataset_id ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">-- 請選擇資料集 --</option>
                {datasets.map(ds => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name} ({ds.stats?.total_images || 0} 張圖片, {ds.stats?.num_classes || 0} 個類別)
                  </option>
                ))}
              </select>
              {errors.dataset_id && (
                <p className="mt-1 text-sm text-red-600">{errors.dataset_id}</p>
              )}
              {loadingDatasets && (
                <p className="mt-1 text-sm text-blue-600">載入資料集列表中...</p>
              )}
              {!loadingDatasets && datasets.length === 0 && (
                <p className="mt-1 text-sm text-yellow-600">⚠️ 尚無可用資料集，請先創建資料集</p>
              )}
            </div>

            {/* 分隔線 */}
            {formData.dataset_id && (
              <div className="border-t pt-4">
                <p className="text-sm text-gray-600 mb-3">📝 以下路徑已自動填充，可視需要修改</p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data YAML 路徑 *
              </label>
              <input
                type="text"
                name="data_yaml"
                value={formData.data_yaml}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.data_yaml ? 'border-red-500' : 'border-gray-300'
                } ${formData.dataset_id ? 'bg-blue-50' : ''}`}
                placeholder="/path/to/data.yaml"
                readOnly={!!formData.dataset_id}
              />
              {errors.data_yaml && (
                <p className="mt-1 text-sm text-red-600">{errors.data_yaml}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                訓練集路徑
              </label>
              <input
                type="text"
                name="train_path"
                value={formData.train_path}
                onChange={handleChange}
                className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  formData.dataset_id ? 'bg-blue-50' : ''
                }`}
                placeholder="/path/to/images/train"
                readOnly={!!formData.dataset_id}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                驗證集路徑
              </label>
              <input
                type="text"
                name="val_path"
                value={formData.val_path}
                onChange={handleChange}
                className={`w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  formData.dataset_id ? 'bg-blue-50' : ''
                }`}
                placeholder="/path/to/images/val"
                readOnly={!!formData.dataset_id}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                類別名稱 (逗號分隔，可選)
              </label>
              <input
                type="text"
                name="class_names"
                value={formData.class_names}
                onChange={handleChange}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  errors.class_names ? 'border-red-500' : 'border-gray-300'
                } ${formData.dataset_id ? 'bg-blue-50' : ''}`}
                placeholder="例如：helmet, person, vehicle"
                readOnly={!!formData.dataset_id}
              />
              {errors.class_names && (
                <p className="mt-1 text-sm text-red-600">{errors.class_names}</p>
              )}
              {!formData.class_names && formData.dataset_id && (
                <p className="mt-1 text-sm text-gray-500">
                  💡 類別資訊將從 data.yaml 讀取
                </p>
              )}
            </div>
          </div>
        )}

        {/* Step 4: 進階選項 */}
        {step === 4 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">進階選項</h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Optimizer
                </label>
                <select
                  name="optimizer"
                  value={formData.optimizer}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="AdamW">AdamW (推薦)</option>
                  <option value="Adam">Adam</option>
                  <option value="SGD">SGD</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Patience
                </label>
                <input
                  type="number"
                  name="patience"
                  value={formData.patience}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">早停耐心值</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Learning Rate (lr0)
              </label>
              <input
                type="number"
                name="lr0"
                value={formData.lr0}
                onChange={handleChange}
                step="0.0001"
                min="0"
                max="1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="cosine_lr"
                name="cosine_lr"
                checked={formData.cosine_lr}
                onChange={handleChange}
                className="w-4 h-4 text-blue-600"
              />
              <label htmlFor="cosine_lr" className="text-sm font-medium text-gray-700">
                使用 Cosine Learning Rate Scheduler
              </label>
            </div>

            <div className="border-t pt-4">
              <div className="flex items-center space-x-2 mb-4">
                <input
                  type="checkbox"
                  id="augment"
                  name="augment"
                  checked={formData.augment}
                  onChange={handleChange}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="augment" className="text-sm font-medium text-gray-700">
                  啟用資料增強
                </label>
              </div>

              {formData.augment && (
                <div className="grid grid-cols-3 gap-4 pl-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      旋轉角度
                    </label>
                    <input
                      type="number"
                      name="degrees"
                      value={formData.degrees}
                      onChange={handleChange}
                      step="0.1"
                      min="0"
                      max="180"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      水平翻轉機率
                    </label>
                    <input
                      type="number"
                      name="flipLR"
                      value={formData.flipLR}
                      onChange={handleChange}
                      step="0.1"
                      min="0"
                      max="1"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Mosaic 機率
                    </label>
                    <input
                      type="number"
                      name="mosaic"
                      value={formData.mosaic}
                      onChange={handleChange}
                      step="0.1"
                      min="0"
                      max="1"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 按鈕 */}
        <div className="flex justify-between pt-6 border-t">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={handlePrev}
                className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                上一步
              </button>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              取消
            </button>

            {step < 4 ? (
              <button
                type="button"
                onClick={handleNext}
                className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                下一步
              </button>
            ) : (
              <button
                type="submit"
                className="px-6 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors font-semibold"
              >
                開始訓練
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

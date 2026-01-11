import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';
import TrainingPage from './pages/TrainingPage';
import DatasetsPage from './pages/DatasetsPage';
import ModelsPage from './pages/ModelsPage';

// 首頁組件
function HomePage() {
  const [apiStatus, setApiStatus] = useState('檢查中...');

  // 檢查後端 API 連線
  const checkAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/');
      const data = await response.json();
      setApiStatus(`✅ ${data.message}`);
    } catch (error) {
      setApiStatus('❌ 無法連接後端 API');
    }
  };

  // 組件掛載時檢查 API
  useEffect(() => {
    checkAPI();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Header */}
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            🎯 YOLO 全端影像辨識系統
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            基於專家會議共識開發的完整物件偵測系統
          </p>

          {/* Status Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">系統狀態</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span className="text-gray-700">前端狀態</span>
                <span className="text-green-600 font-semibold">✅ 運行中</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                <span className="text-gray-700">後端 API</span>
                <span className="text-gray-700 font-semibold">{apiStatus}</span>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {[
              {
                icon: '🏋️',
                title: '模型訓練',
                desc: '支援 YOLOv5/v8/v11 訓練',
                link: '/training',
              },
              { icon: '📹', title: '即時偵測', desc: 'WebSocket 串流偵測', link: null },
              { icon: '📁', title: '資料集管理', desc: '上傳與預處理資料集', link: '/datasets' },
              { icon: '🤖', title: '模型管理', desc: '切換與管理訓練模型', link: '/models' },
              { icon: '📊', title: '訓練監控', desc: '即時查看訓練進度', link: '/training' },
              { icon: '⚡', title: '效能優化', desc: 'ProcessPoolExecutor 加速', link: null },
            ].map((feature, index) => (
              <Link
                key={index}
                to={feature.link || '#'}
                className={`bg-white rounded-lg shadow p-6 hover:shadow-xl transition-all ${
                  feature.link
                    ? 'cursor-pointer hover:scale-105'
                    : 'opacity-60 cursor-not-allowed'
                }`}
                onClick={(e) => !feature.link && e.preventDefault()}
              >
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-sm">{feature.desc}</p>
                {feature.link && (
                  <p className="text-blue-600 text-xs mt-2 font-medium">點擊開始 →</p>
                )}
                {!feature.link && (
                  <p className="text-gray-400 text-xs mt-2">開發中...</p>
                )}
              </Link>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-blue-50 rounded-lg p-8">
            <h3 className="text-2xl font-semibold mb-4 text-gray-800">
              Phase 2 開發中 🚀
            </h3>
            <p className="text-gray-600 mb-4">
              完整的訓練、資料集與模型管理系統已上線！開始建立您的 YOLO 工作流程
            </p>
            <div className="flex justify-center space-x-3">
              <Link
                to="/datasets"
                className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                資料集管理 →
              </Link>
              <Link
                to="/training"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                開始訓練 →
              </Link>
              <Link
                to="/models"
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                模型管理 →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 導航欄組件
function Navbar() {
  const location = useLocation();

  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold text-gray-800">
            🎯 YOLO System
          </Link>

          <div className="flex space-x-4">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg transition-colors ${
                location.pathname === '/'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              首頁
            </Link>
            <Link
              to="/training"
              className={`px-4 py-2 rounded-lg transition-colors ${
                location.pathname === '/training'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              訓練
            </Link>
            <Link
              to="/datasets"
              className={`px-4 py-2 rounded-lg transition-colors ${
                location.pathname === '/datasets'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              資料集
            </Link>
            <Link
              to="/models"
              className={`px-4 py-2 rounded-lg transition-colors ${
                location.pathname === '/models'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              模型
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

// 主 App 組件
function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/training" element={<TrainingPage />} />
          <Route path="/datasets" element={<DatasetsPage />} />
          <Route path="/models" element={<ModelsPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

import { useState } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState('檢查中...')

  // 檢查後端 API 連線
  const checkAPI = async () => {
    try {
      const response = await fetch('/api/')
      const data = await response.json()
      setApiStatus(`✅ ${data.message}`)
    } catch (error) {
      setApiStatus('❌ 無法連接後端 API')
    }
  }

  // 組件掛載時檢查 API
  useState(() => {
    checkAPI()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Header */}
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            🎯 YOLO 全端影像辨識系統
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            基於專家會議共識開發的完整物件偵測系統
          </p>

          {/* Status Card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-white">
              系統狀態
            </h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="text-gray-700 dark:text-gray-200">前端狀態</span>
                <span className="text-green-600 dark:text-green-400 font-semibold">✅ 運行中</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded">
                <span className="text-gray-700 dark:text-gray-200">後端 API</span>
                <span className="text-gray-700 dark:text-gray-200 font-semibold">{apiStatus}</span>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {[
              { icon: '🏋️', title: '模型訓練', desc: '支援 YOLOv5/v8/v11 訓練' },
              { icon: '📹', title: '即時偵測', desc: 'WebSocket 串流偵測' },
              { icon: '📁', title: '資料集管理', desc: '上傳與預處理資料集' },
              { icon: '🤖', title: '模型管理', desc: '切換與管理訓練模型' },
              { icon: '📊', title: '訓練監控', desc: '即時查看訓練進度' },
              { icon: '⚡', title: '效能優化', desc: 'ProcessPoolExecutor 加速' },
            ].map((feature, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-xl transition-shadow"
              >
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  {feature.desc}
                </p>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="bg-primary/10 dark:bg-primary/20 rounded-lg p-8">
            <h3 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-white">
              開發中... 🚧
            </h3>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              系統架構已建立完成，功能模組正在開發中
            </p>
            <button
              onClick={checkAPI}
              className="bg-primary hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              重新檢查 API 連線
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

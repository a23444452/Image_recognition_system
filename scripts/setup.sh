#!/bin/bash
# 專案初始化腳本

set -e

echo "🚀 初始化 YOLO 全端影像辨識系統..."

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安裝"
    exit 1
fi
echo "✅ Python 3 已安裝"

# 檢查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安裝"
    exit 1
fi
echo "✅ Node.js 已安裝"

# 檢查 Redis
if ! command -v redis-server &> /dev/null; then
    echo "⚠️  Redis 未安裝，請先安裝 Redis"
    echo "macOS: brew install redis"
    echo "Ubuntu: sudo apt-get install redis-server"
fi

# 設定後端
echo ""
echo "📦 設定後端環境..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 後端依賴安裝完成"
cd ..

# 設定前端
echo ""
echo "📦 設定前端環境..."
cd frontend
npm install
echo "✅ 前端依賴安裝完成"
cd ..

# 建立環境變數檔案
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 環境變數檔案已建立"
fi

# 建立必要目錄
mkdir -p models datasets logs

echo ""
echo "✅ 專案初始化完成！"
echo ""
echo "🎯 下一步："
echo "1. 啟動 Redis: redis-server"
echo "2. 啟動後端: cd backend && source venv/bin/activate && python main.py"
echo "3. 啟動前端: cd frontend && npm run dev"
echo "4. 訪問: http://localhost:5173"

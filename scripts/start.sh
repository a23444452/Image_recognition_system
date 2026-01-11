#!/bin/bash
# 啟動所有服務

set -e

echo "🚀 啟動 YOLO 全端影像辨識系統..."

# 檢查 Redis 是否運行
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Redis 未運行，正在啟動..."
    redis-server --daemonize yes
    sleep 2
fi
echo "✅ Redis 運行中"

# 啟動後端（背景）
echo "🔧 啟動後端 API..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "✅ 後端 API 已啟動 (PID: $BACKEND_PID)"
cd ..

# 等待後端啟動
sleep 3

# 啟動前端
echo "🎨 啟動前端..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ 前端已啟動 (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "✅ 所有服務已啟動！"
echo ""
echo "🌐 前端: http://localhost:5173"
echo "🔌 後端 API: http://localhost:8000"
echo "📚 API 文檔: http://localhost:8000/docs"
echo ""
echo "⏹️  停止服務: ./scripts/stop.sh"
echo "   或按 Ctrl+C"

# 保持腳本運行
wait

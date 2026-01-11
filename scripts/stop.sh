#!/bin/bash
# 停止所有服務

echo "🛑 停止所有服務..."

# 停止後端
pkill -f "uvicorn main:app" && echo "✅ 後端已停止" || echo "⚠️  後端未運行"

# 停止前端
pkill -f "vite" && echo "✅ 前端已停止" || echo "⚠️  前端未運行"

# 停止 RQ Worker
pkill -f "rq worker" && echo "✅ RQ Worker 已停止" || echo "⚠️  RQ Worker 未運行"

echo "✅ 清理完成"

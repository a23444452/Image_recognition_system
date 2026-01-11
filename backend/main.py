#!/usr/bin/env python3
"""
YOLO 全端影像辨識系統 - FastAPI 主程式
基於專家會議共識開發
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from redis import Redis

from models.database import init_database
from routers import training, websocket, datasets, models

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理
    - 啟動時：載入模型、初始化資料庫連線
    - 關閉時：清理資源
    """
    logger.info("🚀 啟動應用程式...")

    # 初始化資料庫
    try:
        init_database()
        logger.info("✅ 資料庫初始化完成")
    except Exception as e:
        logger.error(f"❌ 資料庫初始化失敗: {e}")
        raise

    # 檢查 Redis 連線
    try:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_conn = Redis(host=redis_host, port=redis_port)
        redis_conn.ping()
        logger.info(f"✅ Redis 連線成功: {redis_host}:{redis_port}")
    except Exception as e:
        logger.warning(f"⚠️  Redis 連線失敗: {e}")
        logger.warning("⚠️  訓練功能將無法使用，請確認 Redis 服務運行中")

    # TODO: 預載入 YOLO 模型（Phase 2）
    # app.state.detection_model = YOLO("models/best.pt")

    logger.info("✅ 應用程式啟動完成")
    yield

    logger.info("🛑 關閉應用程式...")
    # 清理資源
    try:
        if 'redis_conn' in locals():
            redis_conn.close()
            logger.info("✅ Redis 連線已關閉")
    except Exception as e:
        logger.error(f"清理資源時出錯: {e}")

    logger.info("✅ 資源清理完成")


# 初始化 FastAPI
app = FastAPI(
    title="YOLO 全端影像辨識系統",
    description="整合訓練、推論與即時串流的完整物件偵測系統",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite 開發伺服器
        "http://localhost:3000",  # 可能的替代端口
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康檢查端點
@app.get("/")
async def root():
    """系統狀態檢查"""
    return {
        "status": "healthy",
        "message": "YOLO 全端影像辨識系統",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """詳細健康檢查"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "redis": "pending",  # TODO: 實際檢查 Redis
            "database": "pending"  # TODO: 實際檢查資料庫
        }
    }


# 註冊 Routers
app.include_router(training.router, prefix="/api/v1/training", tags=["Training"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])

# TODO: Phase 2C - 註冊其他 Routers
# from routers import streaming
# app.include_router(streaming.router, prefix="/api/v1/streaming", tags=["Streaming"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

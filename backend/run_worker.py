#!/usr/bin/env python3
"""
RQ Worker 啟動腳本
用於處理訓練任務隊列
"""

import os
import sys
import logging
from redis import Redis
from rq import Worker, Queue

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """啟動 RQ Worker"""
    # 從環境變數讀取 Redis 配置
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))

    logger.info(f"🔌 連線到 Redis: {redis_host}:{redis_port}")

    try:
        # 建立 Redis 連線
        redis_conn = Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=False
        )

        # 測試連線
        redis_conn.ping()
        logger.info("✅ Redis 連線成功")

        # 建立隊列
        queue = Queue('training', connection=redis_conn)
        logger.info(f"📋 監聽隊列: training")

        # 建立 Worker
        worker = Worker(
            [queue],
            connection=redis_conn,
            name=f"training-worker-{os.getpid()}"
        )

        logger.info(f"🚀 Worker 啟動: {worker.name}")
        logger.info("⏳ 等待任務...")

        # 啟動 Worker（阻塞）
        worker.work(with_scheduler=True)

    except KeyboardInterrupt:
        logger.info("\n⚠️  收到中斷訊號，正在關閉 Worker...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Worker 啟動失敗: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

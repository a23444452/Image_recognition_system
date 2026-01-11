"""
WebSocket Router for Real-time Training Progress
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
import logging
import asyncio
import json
from redis import Redis

from models.database import get_db
from models.training import TrainingTask

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """WebSocket 連線管理器"""

    def __init__(self):
        # task_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str):
        """接受 WebSocket 連線"""
        await websocket.accept()

        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = set()
            self.active_connections[task_id].add(websocket)

        logger.info(f"📡 WebSocket 連線: task_id={task_id}, 總連線數={len(self.active_connections[task_id])}")

    async def disconnect(self, websocket: WebSocket, task_id: str):
        """移除 WebSocket 連線"""
        async with self._lock:
            if task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]

        logger.info(f"📡 WebSocket 斷線: task_id={task_id}")

    async def broadcast(self, task_id: str, message: dict):
        """廣播訊息給所有訂閱該任務的客戶端"""
        async with self._lock:
            if task_id not in self.active_connections:
                return

            connections = list(self.active_connections[task_id])

        # 廣播給所有連線
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"廣播失敗: {e}")
                disconnected.append(connection)

        # 清理斷線的連線
        if disconnected:
            async with self._lock:
                if task_id in self.active_connections:
                    for conn in disconnected:
                        self.active_connections[task_id].discard(conn)

    def get_connection_count(self, task_id: str) -> int:
        """取得指定任務的連線數"""
        return len(self.active_connections.get(task_id, set()))


# 全域連線管理器
manager = ConnectionManager()


def get_redis() -> Redis:
    """取得 Redis 連線"""
    import os
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    return Redis(host=redis_host, port=redis_port, decode_responses=True)


async def poll_training_progress(
    websocket: WebSocket,
    task_id: str,
    db: Session,
    poll_interval: float = 0.5
):
    """
    輪詢訓練進度並推送到 WebSocket

    根據會議共識：0.5 秒節流避免過度推送

    Args:
        websocket: WebSocket 連線
        task_id: 任務 ID
        db: 資料庫 session
        poll_interval: 輪詢間隔（秒）
    """
    last_epoch = None
    last_loss = None
    last_map = None
    last_status = None

    try:
        while True:
            # 查詢任務狀態
            task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

            if not task:
                await websocket.send_json({
                    "type": "error",
                    "message": f"任務不存在: {task_id}"
                })
                break

            # 檢查是否有變更（避免無意義推送）
            has_change = (
                last_epoch != task.current_epoch or
                last_loss != task.current_loss or
                last_map != task.current_map or
                last_status != task.status.value
            )

            if has_change:
                # 計算進度百分比
                progress = 0
                if task.total_epochs > 0:
                    progress = (task.current_epoch / task.total_epochs) * 100

                # 推送進度更新
                await websocket.send_json({
                    "type": "progress",
                    "data": {
                        "task_id": task.id,
                        "status": task.status.value,
                        "current_epoch": task.current_epoch,
                        "total_epochs": task.total_epochs,
                        "progress": round(progress, 2),
                        "current_loss": task.current_loss,
                        "current_map": task.current_map,
                        "error_message": task.error_message
                    }
                })

                # 更新快取
                last_epoch = task.current_epoch
                last_loss = task.current_loss
                last_map = task.current_map
                last_status = task.status.value

            # 如果任務已完成或失敗，發送最終訊息並結束
            if task.status.value in ['completed', 'failed', 'stopped']:
                await websocket.send_json({
                    "type": "finished",
                    "data": {
                        "task_id": task.id,
                        "status": task.status.value,
                        "model_path": task.model_path,
                        "save_dir": task.save_dir,
                        "error_message": task.error_message
                    }
                })
                logger.info(f"✅ 任務 {task_id} 已完成，結束 WebSocket 推送")
                break

            # 等待下一次輪詢
            await asyncio.sleep(poll_interval)

    except asyncio.CancelledError:
        logger.info(f"WebSocket 輪詢被取消: {task_id}")
    except Exception as e:
        logger.error(f"輪詢錯誤: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"伺服器錯誤: {str(e)}"
        })


@router.websocket("/training/{task_id}")
async def websocket_training_progress(
    websocket: WebSocket,
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    訓練進度 WebSocket 端點

    根據會議共識：
    - 連線到 /ws/training/{task_id}
    - 0.5 秒節流推送進度
    - 即時推送 epoch、loss、mAP 等指標

    Args:
        websocket: WebSocket 連線
        task_id: 任務 ID
        db: 資料庫 session
    """
    await manager.connect(websocket, task_id)

    try:
        # 發送連線成功訊息
        await websocket.send_json({
            "type": "connected",
            "message": f"已連線到任務: {task_id}"
        })

        # 開始輪詢進度
        await poll_training_progress(websocket, task_id, db)

    except WebSocketDisconnect:
        logger.info(f"客戶端主動斷線: {task_id}")

    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}", exc_info=True)

    finally:
        await manager.disconnect(websocket, task_id)


@router.get("/connections/{task_id}")
async def get_connection_info(task_id: str):
    """
    取得指定任務的 WebSocket 連線數（調試用）

    Args:
        task_id: 任務 ID

    Returns:
        dict: 連線資訊
    """
    return {
        "task_id": task_id,
        "connection_count": manager.get_connection_count(task_id)
    }

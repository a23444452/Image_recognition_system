"""
訓練任務管理 API Router
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/start")
async def start_training():
    """
    啟動訓練任務

    根據會議共識：
    1. 驗證資料集與模型路徑
    2. 建立任務記錄 (DB)
    3. 推送到 RQ 隊列（不阻塞）
    """
    # TODO: 實作訓練啟動邏輯
    return {"message": "Training endpoint - To be implemented"}


@router.get("/{task_id}")
async def get_training_status(task_id: str):
    """查詢訓練任務狀態"""
    # TODO: 從資料庫查詢任務狀態
    return {"task_id": task_id, "status": "pending"}


@router.delete("/{task_id}")
async def stop_training(task_id: str):
    """停止訓練任務"""
    # TODO: 實作停止訓練邏輯
    return {"message": f"Stopped training {task_id}"}


@router.get("/tasks")
async def list_training_tasks():
    """列出所有訓練任務"""
    # TODO: 從資料庫列出所有任務
    return {"tasks": []}

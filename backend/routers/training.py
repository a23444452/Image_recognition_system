"""
訓練任務管理 API Router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from redis import Redis

from models.database import get_db
from models.training import TrainingTask, TrainingStatus
from services.training_service import TrainingService
from schemas.training import TrainingConfig, TrainingTaskResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_redis() -> Redis:
    """取得 Redis 連線"""
    from redis import Redis
    import os

    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', 6379))

    return Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=False
    )


def get_training_service(redis: Redis = Depends(get_redis)) -> TrainingService:
    """取得訓練服務實例"""
    return TrainingService(redis)


@router.post("/start", response_model=TrainingTaskResponse)
async def start_training(
    config: TrainingConfig,
    db: Session = Depends(get_db),
    service: TrainingService = Depends(get_training_service)
):
    """
    啟動訓練任務

    根據會議共識：
    1. 驗證資料集與模型路徑
    2. 建立任務記錄 (DB)
    3. 推送到 RQ 隊列（不阻塞）

    Args:
        config: 訓練配置
        db: 資料庫 session
        service: 訓練服務

    Returns:
        TrainingTaskResponse: 創建的訓練任務
    """
    try:
        # 將 Pydantic 模型轉為字典
        config_dict = config.dict()

        # 創建訓練任務
        task = service.create_training_task(db, config_dict)

        logger.info(f"✅ 訓練任務已創建: {task.id}")

        return task.to_dict()

    except Exception as e:
        logger.error(f"創建訓練任務失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"創建訓練任務失敗: {str(e)}")


@router.get("/{task_id}", response_model=TrainingTaskResponse)
async def get_training_status(
    task_id: str,
    db: Session = Depends(get_db),
    service: TrainingService = Depends(get_training_service)
):
    """
    查詢訓練任務狀態

    Args:
        task_id: 任務 ID
        db: 資料庫 session
        service: 訓練服務

    Returns:
        TrainingTaskResponse: 訓練任務詳情
    """
    task = service.get_training_task(db, task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"任務不存在: {task_id}")

    return task.to_dict()


@router.delete("/{task_id}")
async def stop_training(
    task_id: str,
    db: Session = Depends(get_db),
    service: TrainingService = Depends(get_training_service)
):
    """
    停止訓練任務

    Args:
        task_id: 任務 ID
        db: 資料庫 session
        service: 訓練服務

    Returns:
        dict: 操作結果
    """
    success = service.stop_training_task(db, task_id)

    if not success:
        raise HTTPException(status_code=400, detail=f"無法停止任務: {task_id}")

    return {"message": f"任務 {task_id} 已停止", "success": True}


@router.get("/", response_model=List[TrainingTaskResponse])
async def list_training_tasks(
    status: Optional[str] = Query(None, description="過濾狀態 (pending/running/completed/failed/stopped)"),
    limit: int = Query(50, ge=1, le=100, description="最大返回數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    service: TrainingService = Depends(get_training_service)
):
    """
    列出所有訓練任務

    Args:
        status: 過濾狀態（可選）
        limit: 最大返回數量
        offset: 偏移量
        db: 資料庫 session
        service: 訓練服務

    Returns:
        List[TrainingTaskResponse]: 訓練任務列表
    """
    # 解析狀態
    status_enum = None
    if status:
        try:
            status_enum = TrainingStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"無效的狀態值: {status}. 有效值: pending, running, completed, failed, stopped"
            )

    tasks = service.list_training_tasks(db, status_enum, limit, offset)

    return [task.to_dict() for task in tasks]


@router.get("/stats/summary")
async def get_training_statistics(
    db: Session = Depends(get_db),
    service: TrainingService = Depends(get_training_service)
):
    """
    取得訓練任務統計資訊

    Args:
        db: 資料庫 session
        service: 訓練服務

    Returns:
        dict: 統計資訊
    """
    stats = service.get_task_statistics(db)
    return stats

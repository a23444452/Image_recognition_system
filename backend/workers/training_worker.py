"""
RQ 訓練 Worker
在背景執行 YOLO 訓練任務
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from engines.yolo_trainer import YOLOTrainer
from models.database import SessionLocal
from models.training import TrainingStatus

logger = logging.getLogger(__name__)


def run_training(task_id: str, config: Dict[str, Any]) -> str:
    """
    執行訓練任務（RQ worker 函數）

    此函數會被 RQ 在背景執行

    Args:
        task_id: 任務 ID
        config: 訓練配置字典

    Returns:
        str: 訓練結果儲存路徑

    Raises:
        Exception: 訓練失敗時拋出例外
    """
    db: Session = SessionLocal()
    trainer = YOLOTrainer()

    try:
        logger.info(f"🚀 開始訓練任務: {task_id}")

        # 載入任務
        from models.training import TrainingTask
        task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

        if not task:
            raise ValueError(f"任務不存在: {task_id}")

        # 更新狀態為 RUNNING
        task.status = TrainingStatus.RUNNING
        from datetime import datetime
        task.started_at = datetime.now()
        db.commit()

        # 定義進度回調
        def progress_callback(epoch: int, metrics: Dict[str, float]):
            """更新訓練進度到資料庫"""
            try:
                task.current_epoch = epoch
                task.current_loss = metrics.get('loss', task.current_loss)
                task.current_map = metrics.get('mAP', task.current_map)
                db.commit()

                logger.info(
                    f"📊 任務 {task_id} - Epoch {epoch}/{task.total_epochs}, "
                    f"Loss: {task.current_loss:.4f}, mAP: {task.current_map:.4f}"
                )
            except Exception as e:
                logger.error(f"更新進度失敗: {e}")

        # 定義日誌回調
        def log_callback(message: str):
            """記錄訓練日誌"""
            logger.info(f"[{task_id}] {message}")

        # 執行訓練
        save_dir = trainer.train(
            config=config,
            progress_callback=progress_callback,
            log_callback=log_callback
        )

        # 更新狀態為 COMPLETED
        task.status = TrainingStatus.COMPLETED
        task.save_dir = save_dir
        task.model_path = f"{save_dir}/weights/best.pt"
        task.completed_at = datetime.now()
        db.commit()

        logger.info(f"✅ 訓練任務完成: {task_id}, 結果: {save_dir}")

        return save_dir

    except Exception as e:
        logger.error(f"❌ 訓練任務失敗: {task_id}, 錯誤: {e}", exc_info=True)

        # 更新狀態為 FAILED
        try:
            from models.training import TrainingTask
            task = db.query(TrainingTask).filter(TrainingTask.id == task_id).first()
            if task:
                task.status = TrainingStatus.FAILED
                task.error_message = str(e)
                from datetime import datetime
                task.completed_at = datetime.now()
                db.commit()
        except Exception as update_error:
            logger.error(f"更新失敗狀態時出錯: {update_error}")

        raise

    finally:
        db.close()


def get_worker_status() -> Dict[str, Any]:
    """
    取得 Worker 狀態資訊

    Returns:
        Dict[str, Any]: Worker 狀態
    """
    import os
    import psutil

    process = psutil.Process(os.getpid())

    return {
        'pid': process.pid,
        'cpu_percent': process.cpu_percent(interval=0.1),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'status': process.status(),
        'create_time': process.create_time()
    }

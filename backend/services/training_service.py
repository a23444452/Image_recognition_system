"""
訓練服務業務邏輯層
負責訓練任務的 CRUD 操作與 RQ 任務調度
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from redis import Redis
from rq import Queue
from rq.job import Job

from models.training import TrainingTask, TrainingStatus
from models.database import get_db

logger = logging.getLogger(__name__)


class TrainingService:
    """訓練服務類別"""

    def __init__(self, redis_conn: Redis):
        """
        初始化訓練服務

        Args:
            redis_conn: Redis 連線實例
        """
        self.queue = Queue('training', connection=redis_conn)
        self.redis = redis_conn

    def create_training_task(
        self,
        db: Session,
        config: Dict[str, Any]
    ) -> TrainingTask:
        """
        創建訓練任務並加入 RQ 隊列

        Args:
            db: 資料庫 session
            config: 訓練配置字典

        Returns:
            TrainingTask: 創建的訓練任務
        """
        # 生成任務 ID
        task_id = str(uuid.uuid4())

        # 創建資料庫記錄
        task = TrainingTask(
            id=task_id,
            project_name=config.get('project_name', 'yolo_project'),
            model_name=config.get('model_name', 'training'),
            yolo_version=config.get('yolo_version', 'v11'),
            status=TrainingStatus.PENDING,
            config=config,
            total_epochs=config.get('epochs', 100)
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 加入 RQ 隊列
        try:
            from workers.training_worker import run_training

            job = self.queue.enqueue(
                run_training,
                task_id=task_id,
                config=config,
                job_timeout='24h',  # 24 小時超時
                result_ttl=86400,   # 結果保留 1 天
                failure_ttl=86400   # 失敗訊息保留 1 天
            )

            # 更新 job_id
            task.job_id = job.id
            db.commit()

            logger.info(f"✅ 訓練任務已創建: {task_id}, RQ Job: {job.id}")

        except Exception as e:
            logger.error(f"加入 RQ 隊列失敗: {e}", exc_info=True)
            task.status = TrainingStatus.FAILED
            task.error_message = f"加入任務隊列失敗: {str(e)}"
            db.commit()
            raise

        return task

    def get_training_task(
        self,
        db: Session,
        task_id: str
    ) -> Optional[TrainingTask]:
        """
        取得訓練任務

        Args:
            db: 資料庫 session
            task_id: 任務 ID

        Returns:
            Optional[TrainingTask]: 訓練任務或 None
        """
        return db.query(TrainingTask).filter(TrainingTask.id == task_id).first()

    def list_training_tasks(
        self,
        db: Session,
        status: Optional[TrainingStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TrainingTask]:
        """
        列出訓練任務

        Args:
            db: 資料庫 session
            status: 過濾狀態（可選）
            limit: 最大返回數量
            offset: 偏移量

        Returns:
            List[TrainingTask]: 訓練任務列表
        """
        query = db.query(TrainingTask)

        if status:
            query = query.filter(TrainingTask.status == status)

        query = query.order_by(TrainingTask.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_task_progress(
        self,
        db: Session,
        task_id: str,
        current_epoch: int,
        current_loss: Optional[float] = None,
        current_map: Optional[float] = None
    ) -> Optional[TrainingTask]:
        """
        更新訓練任務進度

        Args:
            db: 資料庫 session
            task_id: 任務 ID
            current_epoch: 當前 epoch
            current_loss: 當前 loss
            current_map: 當前 mAP

        Returns:
            Optional[TrainingTask]: 更新後的任務
        """
        task = self.get_training_task(db, task_id)
        if not task:
            logger.warning(f"任務不存在: {task_id}")
            return None

        task.current_epoch = current_epoch
        if current_loss is not None:
            task.current_loss = current_loss
        if current_map is not None:
            task.current_map = current_map

        db.commit()
        db.refresh(task)

        return task

    def update_task_status(
        self,
        db: Session,
        task_id: str,
        status: TrainingStatus,
        error_message: Optional[str] = None,
        model_path: Optional[str] = None,
        save_dir: Optional[str] = None
    ) -> Optional[TrainingTask]:
        """
        更新訓練任務狀態

        Args:
            db: 資料庫 session
            task_id: 任務 ID
            status: 新狀態
            error_message: 錯誤訊息（可選）
            model_path: 模型路徑（可選）
            save_dir: 結果目錄（可選）

        Returns:
            Optional[TrainingTask]: 更新後的任務
        """
        task = self.get_training_task(db, task_id)
        if not task:
            logger.warning(f"任務不存在: {task_id}")
            return None

        old_status = task.status
        task.status = status

        # 更新時間戳
        if status == TrainingStatus.RUNNING and old_status == TrainingStatus.PENDING:
            task.started_at = datetime.now()
        elif status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.STOPPED]:
            task.completed_at = datetime.now()

        # 更新其他欄位
        if error_message:
            task.error_message = error_message
        if model_path:
            task.model_path = model_path
        if save_dir:
            task.save_dir = save_dir

        db.commit()
        db.refresh(task)

        logger.info(f"任務 {task_id} 狀態更新: {old_status.value} → {status.value}")

        return task

    def stop_training_task(
        self,
        db: Session,
        task_id: str
    ) -> bool:
        """
        停止訓練任務

        Args:
            db: 資料庫 session
            task_id: 任務 ID

        Returns:
            bool: 是否成功停止
        """
        task = self.get_training_task(db, task_id)
        if not task:
            logger.warning(f"任務不存在: {task_id}")
            return False

        if task.status not in [TrainingStatus.PENDING, TrainingStatus.RUNNING]:
            logger.warning(f"任務 {task_id} 狀態為 {task.status.value}，無法停止")
            return False

        # 取消 RQ job
        if task.job_id:
            try:
                job = Job.fetch(task.job_id, connection=self.redis)
                job.cancel()
                logger.info(f"RQ Job {task.job_id} 已取消")
            except Exception as e:
                logger.error(f"取消 RQ Job 失敗: {e}")

        # 更新狀態
        self.update_task_status(db, task_id, TrainingStatus.STOPPED)

        return True

    def get_task_statistics(self, db: Session) -> Dict[str, Any]:
        """
        取得訓練任務統計資訊

        Args:
            db: 資料庫 session

        Returns:
            Dict[str, Any]: 統計資訊
        """
        total = db.query(TrainingTask).count()
        pending = db.query(TrainingTask).filter(
            TrainingTask.status == TrainingStatus.PENDING
        ).count()
        running = db.query(TrainingTask).filter(
            TrainingTask.status == TrainingStatus.RUNNING
        ).count()
        completed = db.query(TrainingTask).filter(
            TrainingTask.status == TrainingStatus.COMPLETED
        ).count()
        failed = db.query(TrainingTask).filter(
            TrainingTask.status == TrainingStatus.FAILED
        ).count()

        return {
            'total': total,
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed
        }

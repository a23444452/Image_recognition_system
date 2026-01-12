"""
訓練任務資料庫模型
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base


class TrainingStatus(str, enum.Enum):
    """訓練任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TrainingTask(Base):
    """訓練任務模型"""
    __tablename__ = "training_tasks"

    # 主鍵
    id = Column(String, primary_key=True, index=True)

    # 任務基本資訊
    project_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    yolo_version = Column(String, nullable=False)  # v5, v8, v11

    # 狀態
    status = Column(SQLEnum(TrainingStatus), default=TrainingStatus.PENDING, index=True)
    job_id = Column(String, nullable=True)  # RQ Job ID

    # 訓練配置（JSON 格式儲存）
    config = Column(JSON, nullable=False)

    # 訓練進度
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer, nullable=False)
    current_loss = Column(Float, nullable=True)
    current_map = Column(Float, nullable=True)

    # 結果
    model_path = Column(String, nullable=True)  # 訓練完成的模型路徑
    save_dir = Column(String, nullable=True)    # 結果儲存目錄
    error_message = Column(String, nullable=True)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """轉換為字典"""
        # 從 config 中提取 dataset_id（如果存在）
        dataset_id = self.config.get('dataset_id', '') if self.config else ''

        # 計算進度百分比
        progress_percent = 0
        if self.total_epochs and self.total_epochs > 0:
            progress_percent = int((self.current_epoch / self.total_epochs) * 100)

        return {
            "id": self.id,
            "task_name": self.project_name,  # 映射到 task_name
            "model_type": self.yolo_version,  # 映射到 model_type
            "model_size": "n",  # 預設使用 n (nano) 模型
            "dataset_id": dataset_id,  # 從 config 提取
            "yolo_version": self.yolo_version,
            "status": self.status.value if isinstance(self.status, TrainingStatus) else self.status,
            "job_id": self.job_id,
            "config": self.config,
            "progress": progress_percent,  # 轉為百分比整數
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "best_map": self.current_map,  # 映射到 best_map
            "model_path": self.model_path,
            "save_dir": self.save_dir,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Dataset(Base):
    """資料集模型"""
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # 路徑
    path = Column(String, nullable=False)
    train_path = Column(String, nullable=False)
    val_path = Column(String, nullable=False)
    yaml_path = Column(String, nullable=True)  # data.yaml 檔案路徑

    # 統計資訊
    total_images = Column(Integer, default=0)
    total_labels = Column(Integer, default=0)
    num_classes = Column(Integer, default=0)
    class_names = Column(JSON, nullable=True)  # 類別名稱列表

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "train_path": self.train_path,
            "val_path": self.val_path,
            "yaml_path": self.yaml_path,
            "stats": {
                "total_images": self.total_images,
                "total_labels": self.total_labels,
                "num_classes": self.num_classes,
                "class_names": self.class_names,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Model(Base):
    """模型模型"""
    __tablename__ = "models"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # 模型資訊
    yolo_version = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes

    # 訓練來源
    training_task_id = Column(String, nullable=True)  # 關聯的訓練任務

    # 效能指標
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)

    # 狀態
    is_active = Column(Integer, default=0)  # 是否為當前啟用模型

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """轉換為字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "yolo_version": self.yolo_version,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "training_task_id": self.training_task_id,
            "metrics": {
                "map50": self.map50,
                "map50_95": self.map50_95,
                "precision": self.precision,
                "recall": self.recall,
            },
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

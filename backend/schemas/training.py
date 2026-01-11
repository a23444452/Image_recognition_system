"""
訓練任務相關的 Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class YOLOVersion(str, Enum):
    """YOLO 版本選擇"""
    V5 = "v5"
    V8 = "v8"
    V11 = "v11"


class TrainingStatus(str, Enum):
    """訓練任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TrainingConfig(BaseModel):
    """訓練配置"""
    dataset_id: str = Field(..., description="資料集 ID")
    yolo_version: YOLOVersion = Field(YOLOVersion.V11, description="YOLO 版本")
    epochs: int = Field(100, ge=10, le=300, description="訓練輪數")
    batch_size: int = Field(8, ge=1, le=64, description="批次大小")
    img_size: int = Field(640, ge=320, le=1280, description="圖片尺寸")

    # 進階設定
    device: str = Field("auto", description="訓練裝置 (auto/cpu/gpu)")
    workers: int = Field(4, ge=1, le=16, description="資料載入執行緒數")
    optimizer: str = Field("AdamW", description="優化器")
    patience: int = Field(20, ge=5, le=100, description="Early Stopping 耐心值")

    # 學習率設定
    lr0: float = Field(0.001, gt=0, le=1, description="初始學習率")
    cosine_lr: bool = Field(True, description="使用餘弦退火")

    # 資料增強
    augment: bool = Field(True, description="啟用資料增強")
    degrees: float = Field(10.0, ge=0, le=360, description="旋轉角度範圍")
    flipLR: float = Field(0.5, ge=0, le=1, description="左右翻轉機率")
    mosaic: float = Field(1.0, ge=0, le=1, description="馬賽克增強機率")

    class Config:
        use_enum_values = True


class TrainingProgress(BaseModel):
    """訓練進度"""
    task_id: str
    status: TrainingStatus
    current_epoch: int
    total_epochs: int
    current_loss: Optional[float] = None
    current_map: Optional[float] = None
    eta_seconds: Optional[int] = None


class TrainingTask(BaseModel):
    """訓練任務完整資訊"""
    id: str
    config: TrainingConfig
    status: TrainingStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[TrainingProgress] = None
    error_message: Optional[str] = None
    model_path: Optional[str] = None

"""
串流相關 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class StreamingConfig(BaseModel):
    """串流配置"""
    camera_id: int = Field(0, ge=0, description="攝影機 ID")
    model_path: str = Field(..., description="模型檔案路徑")
    conf_threshold: float = Field(0.25, ge=0.0, le=1.0, description="信心度閾值")
    iou_threshold: float = Field(0.45, ge=0.0, le=1.0, description="IOU 閾值")
    use_gray: bool = Field(False, description="是否使用灰階")


class StreamingUpdateConfig(BaseModel):
    """更新串流配置"""
    conf_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="信心度閾值")
    iou_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="IOU 閾值")
    use_gray: Optional[bool] = Field(None, description="是否使用灰階")


class StreamingStatus(BaseModel):
    """串流狀態"""
    is_streaming: bool = Field(..., description="是否正在串流")
    camera_id: int = Field(..., description="攝影機 ID")
    model_loaded: bool = Field(..., description="模型是否已載入")
    conf_threshold: float = Field(..., description="信心度閾值")
    iou_threshold: float = Field(..., description="IOU 閾值")
    use_gray: bool = Field(..., description="是否使用灰階")


class DetectionBBox(BaseModel):
    """偵測邊界框"""
    x1: float = Field(..., description="左上角 X")
    y1: float = Field(..., description="左上角 Y")
    x2: float = Field(..., description="右下角 X")
    y2: float = Field(..., description="右下角 Y")


class Detection(BaseModel):
    """偵測結果"""
    class_id: int = Field(..., description="類別 ID")
    class_name: str = Field(..., description="類別名稱")
    confidence: float = Field(..., description="信心度")
    bbox: DetectionBBox = Field(..., description="邊界框")

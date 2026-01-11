"""
模型相關 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ModelCreate(BaseModel):
    """創建模型請求"""
    name: str = Field(..., min_length=1, max_length=255, description="模型名稱")
    yolo_version: str = Field(..., pattern="^(v5|v8|v11)$", description="YOLO 版本")
    file_path: str = Field(..., description="模型檔案路徑")
    description: Optional[str] = Field(None, max_length=1000, description="模型描述")
    training_task_id: Optional[str] = Field(None, description="訓練任務 ID")
    map50: Optional[float] = Field(None, ge=0.0, le=1.0, description="mAP@0.5")
    map50_95: Optional[float] = Field(None, ge=0.0, le=1.0, description="mAP@0.5:0.95")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="精確度")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="召回率")


class ModelUpdate(BaseModel):
    """更新模型請求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="模型名稱")
    description: Optional[str] = Field(None, max_length=1000, description="模型描述")
    map50: Optional[float] = Field(None, ge=0.0, le=1.0, description="mAP@0.5")
    map50_95: Optional[float] = Field(None, ge=0.0, le=1.0, description="mAP@0.5:0.95")
    precision: Optional[float] = Field(None, ge=0.0, le=1.0, description="精確度")
    recall: Optional[float] = Field(None, ge=0.0, le=1.0, description="召回率")


class ModelMetrics(BaseModel):
    """模型指標"""
    map50: Optional[float] = Field(None, description="mAP@0.5")
    map50_95: Optional[float] = Field(None, description="mAP@0.5:0.95")
    precision: Optional[float] = Field(None, description="精確度")
    recall: Optional[float] = Field(None, description="召回率")


class ModelResponse(BaseModel):
    """模型回應"""
    id: str = Field(..., description="模型 ID")
    name: str = Field(..., description="模型名稱")
    description: Optional[str] = Field(None, description="模型描述")
    yolo_version: str = Field(..., description="YOLO 版本")
    file_path: str = Field(..., description="模型檔案路徑")
    file_size: Optional[int] = Field(None, description="檔案大小（bytes）")
    training_task_id: Optional[str] = Field(None, description="訓練任務 ID")
    metrics: ModelMetrics = Field(..., description="效能指標")
    is_active: bool = Field(..., description="是否為啟用模型")
    created_at: Optional[str] = Field(None, description="創建時間")

    class Config:
        from_attributes = True


class ModelComparisonItem(BaseModel):
    """模型比較項目"""
    id: str = Field(..., description="模型 ID")
    name: str = Field(..., description="模型名稱")
    yolo_version: str = Field(..., description="YOLO 版本")
    file_size_mb: Optional[float] = Field(None, description="檔案大小（MB）")
    metrics: ModelMetrics = Field(..., description="效能指標")
    is_active: bool = Field(..., description="是否為啟用模型")
    created_at: Optional[str] = Field(None, description="創建時間")


class ModelComparisonRequest(BaseModel):
    """模型比較請求"""
    model_config = {"protected_namespaces": ()}

    model_ids: List[str] = Field(..., min_items=2, max_items=10, description="模型 ID 列表")


class ModelComparisonResponse(BaseModel):
    """模型比較回應"""
    models: List[ModelComparisonItem] = Field(..., description="模型比較列表")
    count: int = Field(..., description="模型數量")


class ModelStatistics(BaseModel):
    """模型統計資訊"""
    model_config = {"protected_namespaces": ()}

    total: int = Field(..., description="總模型數")
    by_version: Dict[str, int] = Field(..., description="各版本模型數")
    active_model_id: Optional[str] = Field(None, description="當前啟用模型 ID")

"""
資料集相關 Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetCreate(BaseModel):
    """創建資料集請求"""
    name: str = Field(..., min_length=1, max_length=255, description="資料集名稱")
    description: Optional[str] = Field(None, max_length=1000, description="資料集描述")
    source_folder: Optional[str] = Field(None, description="原始資料夾路徑")
    split_ratio: float = Field(0.8, ge=0.0, le=1.0, description="訓練集比例")


class DatasetUpdate(BaseModel):
    """更新資料集請求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="資料集名稱")
    description: Optional[str] = Field(None, max_length=1000, description="資料集描述")


class DatasetStats(BaseModel):
    """資料集統計資訊"""
    total_images: int = Field(..., description="總圖片數")
    total_labels: int = Field(..., description="總標註數")
    num_classes: int = Field(..., description="類別數量")
    class_names: List[str] = Field(..., description="類別名稱列表")


class DatasetResponse(BaseModel):
    """資料集回應"""
    id: str = Field(..., description="資料集 ID")
    name: str = Field(..., description="資料集名稱")
    description: Optional[str] = Field(None, description="資料集描述")
    path: str = Field(..., description="資料集路徑")
    train_path: str = Field(..., description="訓練集路徑")
    val_path: str = Field(..., description="驗證集路徑")
    stats: DatasetStats = Field(..., description="統計資訊")
    created_at: Optional[str] = Field(None, description="創建時間")

    class Config:
        from_attributes = True


class DatasetValidation(BaseModel):
    """資料集驗證結果"""
    valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="錯誤列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    stats: Dict[str, Any] = Field(default_factory=dict, description="統計資訊")


class DatasetDetails(DatasetResponse):
    """資料集詳細資訊"""
    statistics: Dict[str, Any] = Field(..., description="詳細統計資訊")
    validation: DatasetValidation = Field(..., description="驗證結果")


class GenerateYamlRequest(BaseModel):
    """生成 YAML 請求"""
    output_path: Optional[str] = Field(None, description="輸出路徑（可選）")


class GenerateYamlResponse(BaseModel):
    """生成 YAML 回應"""
    yaml_path: str = Field(..., description="YAML 檔案路徑")
    message: str = Field(..., description="訊息")

"""
模型管理 API Router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from models.database import get_db
from services.model_service import ModelService
from schemas.model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelComparisonRequest,
    ModelComparisonResponse,
    ModelStatistics
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_model_service() -> ModelService:
    """取得模型服務實例"""
    return ModelService()


@router.post("/", response_model=ModelResponse, status_code=201)
async def create_model(
    request: ModelCreate,
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    創建模型記錄

    Args:
        request: 創建模型請求
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelResponse: 創建的模型
    """
    try:
        model = service.create_model(
            db=db,
            name=request.name,
            yolo_version=request.yolo_version,
            file_path=request.file_path,
            description=request.description,
            training_task_id=request.training_task_id,
            map50=request.map50,
            map50_95=request.map50_95,
            precision=request.precision,
            recall=request.recall
        )

        logger.info(f"✅ 模型已創建: {model.id}")

        return model.to_dict()

    except Exception as e:
        logger.error(f"創建模型失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"創建模型失敗: {str(e)}")


@router.get("/", response_model=List[ModelResponse])
async def list_models(
    yolo_version: Optional[str] = Query(None, regex="^(v5|v8|v11)$", description="過濾 YOLO 版本"),
    is_active: Optional[bool] = Query(None, description="過濾啟用狀態"),
    limit: int = Query(50, ge=1, le=100, description="最大返回數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    列出所有模型

    Args:
        yolo_version: 過濾 YOLO 版本
        is_active: 過濾啟用狀態
        limit: 最大返回數量
        offset: 偏移量
        db: 資料庫 session
        service: 模型服務

    Returns:
        List[ModelResponse]: 模型列表
    """
    models = service.list_models(db, yolo_version, is_active, limit, offset)
    return [model.to_dict() for model in models]


@router.get("/active", response_model=ModelResponse)
async def get_active_model(
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    取得當前啟用的模型

    Args:
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelResponse: 啟用的模型
    """
    model = service.get_active_model(db)

    if not model:
        raise HTTPException(status_code=404, detail="尚未設定啟用模型")

    return model.to_dict()


@router.get("/statistics", response_model=ModelStatistics)
async def get_model_statistics(
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    取得模型統計資訊

    Args:
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelStatistics: 統計資訊
    """
    stats = service.get_model_statistics(db)
    return stats


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    取得模型資訊

    Args:
        model_id: 模型 ID
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelResponse: 模型資訊
    """
    model = service.get_model(db, model_id)

    if not model:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    return model.to_dict()


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    request: ModelUpdate,
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    更新模型資訊

    Args:
        model_id: 模型 ID
        request: 更新模型請求
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelResponse: 更新後的模型
    """
    model = service.update_model(
        db=db,
        model_id=model_id,
        name=request.name,
        description=request.description,
        map50=request.map50,
        map50_95=request.map50_95,
        precision=request.precision,
        recall=request.recall
    )

    if not model:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    return model.to_dict()


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    delete_file: bool = Query(False, description="是否同時刪除檔案"),
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    刪除模型

    Args:
        model_id: 模型 ID
        delete_file: 是否同時刪除檔案
        db: 資料庫 session
        service: 模型服務

    Returns:
        dict: 操作結果
    """
    success = service.delete_model(db, model_id, delete_file)

    if not success:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    return {
        "message": f"模型 {model_id} 已刪除",
        "deleted_file": delete_file,
        "success": True
    }


@router.post("/{model_id}/activate", response_model=ModelResponse)
async def activate_model(
    model_id: str,
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    啟用模型（同時停用其他模型）

    Args:
        model_id: 模型 ID
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelResponse: 啟用的模型
    """
    model = service.set_active_model(db, model_id)

    if not model:
        raise HTTPException(status_code=404, detail=f"模型不存在: {model_id}")

    return model.to_dict()


@router.post("/compare", response_model=ModelComparisonResponse)
async def compare_models(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db),
    service: ModelService = Depends(get_model_service)
):
    """
    比較多個模型的效能

    Args:
        request: 模型比較請求
        db: 資料庫 session
        service: 模型服務

    Returns:
        ModelComparisonResponse: 模型比較結果
    """
    comparison = service.compare_models(db, request.model_ids)

    if not comparison:
        raise HTTPException(status_code=404, detail="找不到指定的模型")

    return {
        "models": comparison,
        "count": len(comparison)
    }

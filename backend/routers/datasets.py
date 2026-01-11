"""
資料集管理 API Router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from models.database import get_db
from services.dataset_service import DatasetService
from schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetDetails,
    GenerateYamlRequest,
    GenerateYamlResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_dataset_service() -> DatasetService:
    """取得資料集服務實例"""
    return DatasetService()


@router.post("/", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    request: DatasetCreate,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    創建資料集

    Args:
        request: 創建資料集請求
        db: 資料庫 session
        service: 資料集服務

    Returns:
        DatasetResponse: 創建的資料集
    """
    try:
        dataset = service.create_dataset(
            db=db,
            name=request.name,
            description=request.description,
            source_folder=request.source_folder,
            split_ratio=request.split_ratio
        )

        logger.info(f"✅ 資料集已創建: {dataset.id}")

        return dataset.to_dict()

    except ValueError as e:
        logger.error(f"資料集驗證失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"創建資料集失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"創建資料集失敗: {str(e)}")


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    limit: int = Query(50, ge=1, le=100, description="最大返回數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    列出所有資料集

    Args:
        limit: 最大返回數量
        offset: 偏移量
        db: 資料庫 session
        service: 資料集服務

    Returns:
        List[DatasetResponse]: 資料集列表
    """
    datasets = service.list_datasets(db, limit, offset)
    return [dataset.to_dict() for dataset in datasets]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    取得資料集資訊

    Args:
        dataset_id: 資料集 ID
        db: 資料庫 session
        service: 資料集服務

    Returns:
        DatasetResponse: 資料集資訊
    """
    dataset = service.get_dataset(db, dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"資料集不存在: {dataset_id}")

    return dataset.to_dict()


@router.get("/{dataset_id}/details", response_model=DatasetDetails)
async def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    取得資料集詳細資訊（含統計與驗證）

    Args:
        dataset_id: 資料集 ID
        db: 資料庫 session
        service: 資料集服務

    Returns:
        DatasetDetails: 資料集詳細資訊
    """
    details = service.get_dataset_details(db, dataset_id)

    if not details:
        raise HTTPException(status_code=404, detail=f"資料集不存在: {dataset_id}")

    return details


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    request: DatasetUpdate,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    更新資料集資訊

    Args:
        dataset_id: 資料集 ID
        request: 更新資料集請求
        db: 資料庫 session
        service: 資料集服務

    Returns:
        DatasetResponse: 更新後的資料集
    """
    dataset = service.update_dataset(
        db=db,
        dataset_id=dataset_id,
        name=request.name,
        description=request.description
    )

    if not dataset:
        raise HTTPException(status_code=404, detail=f"資料集不存在: {dataset_id}")

    return dataset.to_dict()


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    delete_files: bool = Query(False, description="是否同時刪除檔案"),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    刪除資料集

    Args:
        dataset_id: 資料集 ID
        delete_files: 是否同時刪除檔案
        db: 資料庫 session
        service: 資料集服務

    Returns:
        dict: 操作結果
    """
    success = service.delete_dataset(db, dataset_id, delete_files)

    if not success:
        raise HTTPException(status_code=404, detail=f"資料集不存在: {dataset_id}")

    return {
        "message": f"資料集 {dataset_id} 已刪除",
        "deleted_files": delete_files,
        "success": True
    }


@router.post("/{dataset_id}/generate-yaml", response_model=GenerateYamlResponse)
async def generate_data_yaml(
    dataset_id: str,
    request: GenerateYamlRequest,
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    生成資料集的 data.yaml 檔案

    Args:
        dataset_id: 資料集 ID
        request: 生成 YAML 請求
        db: 資料庫 session
        service: 資料集服務

    Returns:
        GenerateYamlResponse: YAML 檔案路徑
    """
    try:
        yaml_path = service.generate_data_yaml(
            db=db,
            dataset_id=dataset_id,
            output_path=request.output_path
        )

        return {
            "yaml_path": yaml_path,
            "message": "data.yaml 生成成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"生成 data.yaml 失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成 data.yaml 失敗: {str(e)}")


@router.get("/{dataset_id}/samples")
async def get_sample_images(
    dataset_id: str,
    split: str = Query('train', regex='^(train|val)$', description="資料集分割"),
    limit: int = Query(10, ge=1, le=100, description="最大返回數量"),
    db: Session = Depends(get_db),
    service: DatasetService = Depends(get_dataset_service)
):
    """
    取得資料集樣本圖片路徑

    Args:
        dataset_id: 資料集 ID
        split: 'train' 或 'val'
        limit: 最大返回數量
        db: 資料庫 session
        service: 資料集服務

    Returns:
        dict: 樣本圖片路徑列表
    """
    images = service.get_sample_images(db, dataset_id, split, limit)

    if not images and not service.get_dataset(db, dataset_id):
        raise HTTPException(status_code=404, detail=f"資料集不存在: {dataset_id}")

    return {
        "dataset_id": dataset_id,
        "split": split,
        "count": len(images),
        "images": images
    }

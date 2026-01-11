"""
資料集服務業務邏輯層
負責資料集的 CRUD 操作與處理
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
import logging
import os
import shutil
from pathlib import Path

from models.training import Dataset
from utils.dataset_utils import (
    split_dataset,
    validate_dataset,
    get_dataset_statistics,
    create_data_yaml
)

logger = logging.getLogger(__name__)


class DatasetService:
    """資料集服務類別"""

    def __init__(self, base_path: str = "./datasets"):
        """
        初始化資料集服務

        Args:
            base_path: 資料集儲存根目錄
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_dataset(
        self,
        db: Session,
        name: str,
        description: Optional[str] = None,
        source_folder: Optional[str] = None,
        split_ratio: float = 0.8
    ) -> Dataset:
        """
        創建資料集

        Args:
            db: 資料庫 session
            name: 資料集名稱
            description: 資料集描述
            source_folder: 原始資料夾路徑（包含圖片和標註）
            split_ratio: 訓練集比例

        Returns:
            Dataset: 創建的資料集
        """
        dataset_id = str(uuid.uuid4())
        dataset_path = self.base_path / dataset_id

        # 創建資料集目錄
        dataset_path.mkdir(parents=True, exist_ok=True)

        # 如果提供了原始資料夾，進行分割
        if source_folder and os.path.exists(source_folder):
            logger.info(f"分割資料集: {source_folder}")

            try:
                train_count, val_count = split_dataset(
                    source_folder=source_folder,
                    output_folder=str(dataset_path),
                    split_ratio=split_ratio,
                    use_multiprocessing=True
                )

                logger.info(f"資料集分割完成: 訓練集={train_count}, 驗證集={val_count}")

            except Exception as e:
                logger.error(f"資料集分割失敗: {e}", exc_info=True)
                # 清理已創建的目錄
                shutil.rmtree(dataset_path, ignore_errors=True)
                raise

        # 驗證資料集結構
        validation_result = validate_dataset(str(dataset_path))

        if not validation_result['valid']:
            logger.error(f"資料集驗證失敗: {validation_result['errors']}")
            raise ValueError(f"資料集驗證失敗: {', '.join(validation_result['errors'])}")

        # 獲取統計資訊
        stats = get_dataset_statistics(str(dataset_path))

        # 讀取類別名稱
        classes_file = dataset_path / 'classes.txt'
        class_names = []
        if classes_file.exists():
            with open(classes_file, 'r', encoding='utf-8') as f:
                class_names = [line.strip() for line in f if line.strip()]

        # 創建資料庫記錄
        dataset = Dataset(
            id=dataset_id,
            name=name,
            description=description,
            path=str(dataset_path),
            train_path=str(dataset_path / 'images' / 'train'),
            val_path=str(dataset_path / 'images' / 'val'),
            total_images=stats['total_images'],
            total_labels=stats['total_labels'],
            num_classes=len(class_names),
            class_names=class_names
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        logger.info(f"✅ 資料集已創建: {dataset_id}")

        return dataset

    def get_dataset(
        self,
        db: Session,
        dataset_id: str
    ) -> Optional[Dataset]:
        """
        取得資料集

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID

        Returns:
            Optional[Dataset]: 資料集或 None
        """
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()

    def list_datasets(
        self,
        db: Session,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dataset]:
        """
        列出資料集

        Args:
            db: 資料庫 session
            limit: 最大返回數量
            offset: 偏移量

        Returns:
            List[Dataset]: 資料集列表
        """
        query = db.query(Dataset)
        query = query.order_by(Dataset.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_dataset(
        self,
        db: Session,
        dataset_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dataset]:
        """
        更新資料集資訊

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID
            name: 新名稱
            description: 新描述

        Returns:
            Optional[Dataset]: 更新後的資料集
        """
        dataset = self.get_dataset(db, dataset_id)

        if not dataset:
            logger.warning(f"資料集不存在: {dataset_id}")
            return None

        if name is not None:
            dataset.name = name
        if description is not None:
            dataset.description = description

        db.commit()
        db.refresh(dataset)

        logger.info(f"資料集已更新: {dataset_id}")

        return dataset

    def delete_dataset(
        self,
        db: Session,
        dataset_id: str,
        delete_files: bool = False
    ) -> bool:
        """
        刪除資料集

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID
            delete_files: 是否同時刪除檔案

        Returns:
            bool: 是否成功刪除
        """
        dataset = self.get_dataset(db, dataset_id)

        if not dataset:
            logger.warning(f"資料集不存在: {dataset_id}")
            return False

        # 刪除檔案
        if delete_files and os.path.exists(dataset.path):
            try:
                shutil.rmtree(dataset.path)
                logger.info(f"已刪除資料集檔案: {dataset.path}")
            except Exception as e:
                logger.error(f"刪除資料集檔案失敗: {e}")

        # 刪除資料庫記錄
        db.delete(dataset)
        db.commit()

        logger.info(f"資料集已刪除: {dataset_id}")

        return True

    def get_dataset_details(
        self,
        db: Session,
        dataset_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        取得資料集詳細資訊（含統計）

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID

        Returns:
            Optional[Dict[str, Any]]: 資料集詳情
        """
        dataset = self.get_dataset(db, dataset_id)

        if not dataset:
            return None

        # 獲取統計資訊
        stats = get_dataset_statistics(dataset.path)

        # 驗證資料集
        validation = validate_dataset(dataset.path)

        return {
            **dataset.to_dict(),
            'statistics': stats,
            'validation': validation
        }

    def generate_data_yaml(
        self,
        db: Session,
        dataset_id: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成資料集的 data.yaml 檔案

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID
            output_path: 輸出路徑（可選）

        Returns:
            str: data.yaml 檔案路徑
        """
        dataset = self.get_dataset(db, dataset_id)

        if not dataset:
            raise ValueError(f"資料集不存在: {dataset_id}")

        if not output_path:
            output_path = os.path.join(dataset.path, 'data.yaml')

        # 類別名稱字串
        class_names_str = ','.join(dataset.class_names) if dataset.class_names else ''

        yaml_path = create_data_yaml(
            train_path=dataset.train_path,
            val_path=dataset.val_path,
            class_names_str=class_names_str,
            output_path=output_path
        )

        logger.info(f"✅ 已生成 data.yaml: {yaml_path}")

        return yaml_path

    def get_sample_images(
        self,
        db: Session,
        dataset_id: str,
        split: str = 'train',
        limit: int = 10
    ) -> List[str]:
        """
        取得資料集樣本圖片路徑

        Args:
            db: 資料庫 session
            dataset_id: 資料集 ID
            split: 'train' 或 'val'
            limit: 最大返回數量

        Returns:
            List[str]: 圖片路徑列表
        """
        dataset = self.get_dataset(db, dataset_id)

        if not dataset:
            return []

        image_dir = Path(dataset.path) / 'images' / split

        if not image_dir.exists():
            return []

        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        images = [
            str(img)
            for img in image_dir.iterdir()
            if img.suffix.lower() in valid_exts
        ]

        return images[:limit]

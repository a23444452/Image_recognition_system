"""
模型服務業務邏輯層
負責模型的 CRUD 操作與管理
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
import logging
import os
from pathlib import Path

from models.training import Model

logger = logging.getLogger(__name__)


class ModelService:
    """模型服務類別"""

    def __init__(self, base_path: str = "./models"):
        """
        初始化模型服務

        Args:
            base_path: 模型儲存根目錄
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_model(
        self,
        db: Session,
        name: str,
        yolo_version: str,
        file_path: str,
        description: Optional[str] = None,
        training_task_id: Optional[str] = None,
        map50: Optional[float] = None,
        map50_95: Optional[float] = None,
        precision: Optional[float] = None,
        recall: Optional[float] = None
    ) -> Model:
        """
        創建模型記錄

        Args:
            db: 資料庫 session
            name: 模型名稱
            yolo_version: YOLO 版本
            file_path: 模型檔案路徑
            description: 模型描述
            training_task_id: 訓練任務 ID
            map50: mAP@0.5
            map50_95: mAP@0.5:0.95
            precision: 精確度
            recall: 召回率

        Returns:
            Model: 創建的模型
        """
        model_id = str(uuid.uuid4())

        # 獲取檔案大小
        file_size = None
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        # 創建資料庫記錄
        model = Model(
            id=model_id,
            name=name,
            description=description,
            yolo_version=yolo_version,
            file_path=file_path,
            file_size=file_size,
            training_task_id=training_task_id,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall,
            is_active=0
        )

        db.add(model)
        db.commit()
        db.refresh(model)

        logger.info(f"✅ 模型已創建: {model_id}")

        return model

    def get_model(
        self,
        db: Session,
        model_id: str
    ) -> Optional[Model]:
        """
        取得模型

        Args:
            db: 資料庫 session
            model_id: 模型 ID

        Returns:
            Optional[Model]: 模型或 None
        """
        return db.query(Model).filter(Model.id == model_id).first()

    def list_models(
        self,
        db: Session,
        yolo_version: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Model]:
        """
        列出模型

        Args:
            db: 資料庫 session
            yolo_version: 過濾 YOLO 版本
            is_active: 過濾啟用狀態
            limit: 最大返回數量
            offset: 偏移量

        Returns:
            List[Model]: 模型列表
        """
        query = db.query(Model)

        if yolo_version:
            query = query.filter(Model.yolo_version == yolo_version)

        if is_active is not None:
            query = query.filter(Model.is_active == (1 if is_active else 0))

        query = query.order_by(Model.created_at.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    def update_model(
        self,
        db: Session,
        model_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        map50: Optional[float] = None,
        map50_95: Optional[float] = None,
        precision: Optional[float] = None,
        recall: Optional[float] = None
    ) -> Optional[Model]:
        """
        更新模型資訊

        Args:
            db: 資料庫 session
            model_id: 模型 ID
            name: 新名稱
            description: 新描述
            map50: mAP@0.5
            map50_95: mAP@0.5:0.95
            precision: 精確度
            recall: 召回率

        Returns:
            Optional[Model]: 更新後的模型
        """
        model = self.get_model(db, model_id)

        if not model:
            logger.warning(f"模型不存在: {model_id}")
            return None

        if name is not None:
            model.name = name
        if description is not None:
            model.description = description
        if map50 is not None:
            model.map50 = map50
        if map50_95 is not None:
            model.map50_95 = map50_95
        if precision is not None:
            model.precision = precision
        if recall is not None:
            model.recall = recall

        db.commit()
        db.refresh(model)

        logger.info(f"模型已更新: {model_id}")

        return model

    def delete_model(
        self,
        db: Session,
        model_id: str,
        delete_file: bool = False
    ) -> bool:
        """
        刪除模型

        Args:
            db: 資料庫 session
            model_id: 模型 ID
            delete_file: 是否同時刪除檔案

        Returns:
            bool: 是否成功刪除
        """
        model = self.get_model(db, model_id)

        if not model:
            logger.warning(f"模型不存在: {model_id}")
            return False

        # 刪除檔案
        if delete_file and os.path.exists(model.file_path):
            try:
                os.remove(model.file_path)
                logger.info(f"已刪除模型檔案: {model.file_path}")
            except Exception as e:
                logger.error(f"刪除模型檔案失敗: {e}")

        # 刪除資料庫記錄
        db.delete(model)
        db.commit()

        logger.info(f"模型已刪除: {model_id}")

        return True

    def set_active_model(
        self,
        db: Session,
        model_id: str
    ) -> Optional[Model]:
        """
        設定啟用模型（同時停用其他模型）

        Args:
            db: 資料庫 session
            model_id: 模型 ID

        Returns:
            Optional[Model]: 啟用的模型
        """
        model = self.get_model(db, model_id)

        if not model:
            logger.warning(f"模型不存在: {model_id}")
            return None

        # 停用所有模型
        db.query(Model).update({Model.is_active: 0})

        # 啟用指定模型
        model.is_active = 1
        db.commit()
        db.refresh(model)

        logger.info(f"✅ 模型已啟用: {model_id}")

        return model

    def get_active_model(self, db: Session) -> Optional[Model]:
        """
        取得當前啟用的模型

        Args:
            db: 資料庫 session

        Returns:
            Optional[Model]: 啟用的模型或 None
        """
        return db.query(Model).filter(Model.is_active == 1).first()

    def compare_models(
        self,
        db: Session,
        model_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        比較多個模型的效能

        Args:
            db: 資料庫 session
            model_ids: 模型 ID 列表

        Returns:
            List[Dict[str, Any]]: 模型比較結果
        """
        models = [self.get_model(db, mid) for mid in model_ids]
        models = [m for m in models if m is not None]

        if not models:
            return []

        comparison = []
        for model in models:
            comparison.append({
                'id': model.id,
                'name': model.name,
                'yolo_version': model.yolo_version,
                'file_size_mb': round(model.file_size / 1024 / 1024, 2) if model.file_size else None,
                'metrics': {
                    'map50': model.map50,
                    'map50_95': model.map50_95,
                    'precision': model.precision,
                    'recall': model.recall
                },
                'is_active': bool(model.is_active),
                'created_at': model.created_at.isoformat() if model.created_at else None
            })

        return comparison

    def get_model_statistics(self, db: Session) -> Dict[str, Any]:
        """
        取得模型統計資訊

        Args:
            db: 資料庫 session

        Returns:
            Dict[str, Any]: 統計資訊
        """
        total = db.query(Model).count()

        v5_count = db.query(Model).filter(Model.yolo_version == 'v5').count()
        v8_count = db.query(Model).filter(Model.yolo_version == 'v8').count()
        v11_count = db.query(Model).filter(Model.yolo_version == 'v11').count()

        active_model = self.get_active_model(db)

        return {
            'total': total,
            'by_version': {
                'v5': v5_count,
                'v8': v8_count,
                'v11': v11_count
            },
            'active_model_id': active_model.id if active_model else None
        }

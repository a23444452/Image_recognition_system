"""
YOLO 訓練引擎
從 YOLO_No_Code_Training 遷移並改造為 Web API 適用版本
移除 GUI 依賴，改用 RQ 任務隊列
"""

from ultralytics import YOLO
import os
import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class YOLOTrainer:
    """
    YOLO 訓練引擎
    支援 YOLOv5/v8/v11 訓練
    """

    def __init__(self):
        self.model = None

    def train(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[int, Dict], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        訓練 YOLO 模型

        Args:
            config: 訓練配置字典
            progress_callback: 進度回調 callback(epoch, metrics)
            log_callback: 日誌回調 callback(message)

        Returns:
            str: 訓練結果儲存路徑
        """
        # 解析配置
        project_name = config.get('project_name', 'yolo_project')
        model_name = config.get('model_name', 'training')
        version = config.get('yolo_version', 'v11')
        epochs = config.get('epochs', 100)
        batch = config.get('batch_size', 8)
        imgsz = config.get('img_size', 640)
        data_yaml = config.get('data_yaml')

        # 進階超參數
        device_str = config.get('device', 'auto')
        workers = config.get('workers', 4)
        optimizer = config.get('optimizer', 'AdamW')
        patience = config.get('patience', 20)

        # 優化參數
        lr0 = config.get('lr0', 0.001)
        cos_lr = config.get('cosine_lr', True)
        rect = config.get('rect', False)
        cache = config.get('cache', False)

        # 資料增強
        augment = config.get('augment', True)
        degrees = config.get('degrees', 10.0) if augment else 0.0
        fliplr = config.get('flipLR', 0.5) if augment else 0.0
        mosaic = config.get('mosaic', 1.0) if augment else 0.0

        # 映射裝置字串
        device = self._map_device(device_str)

        # 確定基礎模型
        checkpoint = config.get('checkpoint', '')
        if checkpoint and os.path.exists(checkpoint):
            base_model = checkpoint
            if log_callback:
                log_callback(f"📦 從檢查點恢復訓練: {base_model}")
        else:
            base_model = self._get_base_model(version)
            if log_callback:
                log_callback(f"🤖 使用預訓練模型: {base_model}")

        # 初始化模型
        if log_callback:
            log_callback(f"⚙️ 初始化 YOLO {version} 模型...")

        self.model = YOLO(base_model)

        # 附加進度回調
        if progress_callback:
            def on_train_epoch_end(trainer):
                current_epoch = trainer.epoch + 1
                total_epochs = trainer.epochs

                # 提取訓練指標
                metrics = {
                    'loss': float(trainer.loss.item()) if hasattr(trainer, 'loss') else 0.0,
                    'mAP': 0.0,  # TODO: 從 trainer.metrics 提取
                }

                progress_callback(current_epoch, metrics)

            self.model.add_callback("on_train_epoch_end", on_train_epoch_end)

        # 記錄訓練配置
        if log_callback:
            log_callback(f"📊 訓練配置:")
            log_callback(f"  - Epochs: {epochs}, Batch: {batch}, Image Size: {imgsz}")
            log_callback(f"  - Device: {device_str}, Workers: {workers}")
            log_callback(f"  - Optimizer: {optimizer}, Patience: {patience}")
            log_callback(f"  - LR0: {lr0}, Cosine LR: {cos_lr}")
            log_callback(f"  - Augmentation: {augment}")
            if augment:
                log_callback(f"    - Degrees: {degrees}, FlipLR: {fliplr}, Mosaic: {mosaic}")

        # 開始訓練
        if log_callback:
            log_callback(f"🚀 開始訓練 {epochs} 個 epochs...")

        try:
            results = self.model.train(
                data=data_yaml,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                device=device,
                workers=workers,
                optimizer=optimizer,
                patience=patience,
                lr0=lr0,
                cos_lr=cos_lr,
                rect=rect,
                cache=cache,
                degrees=degrees,
                fliplr=fliplr,
                mosaic=mosaic,
                project=project_name,
                name=model_name,
                exist_ok=True,
                verbose=True
            )

            save_dir = str(results.save_dir)

            if log_callback:
                log_callback(f"✅ 訓練完成！")
                log_callback(f"📁 結果儲存在: {save_dir}")

            # 匯出 ONNX（根據會議共識，支援多格式）
            try:
                if log_callback:
                    log_callback(f"📦 匯出 ONNX 格式...")
                self.model.export(format='onnx')
                if log_callback:
                    log_callback(f"✅ ONNX 匯出完成")
            except Exception as e:
                logger.error(f"ONNX 匯出失敗: {e}")
                if log_callback:
                    log_callback(f"⚠️ ONNX 匯出失敗: {e}")

            return save_dir

        except Exception as e:
            logger.error(f"訓練失敗: {e}", exc_info=True)
            if log_callback:
                log_callback(f"❌ 訓練失敗: {e}")
            raise

    def _map_device(self, device_str: str) -> Optional[str]:
        """映射裝置字串到 YOLO 格式"""
        device_map = {
            'cpu': 'cpu',
            'gpu': '0',
            'cuda': '0',
            'mps': 'mps',
            'auto': None
        }
        return device_map.get(device_str.lower(), None)

    def _get_base_model(self, version: str) -> str:
        """根據版本選擇預訓練模型"""
        model_map = {
            'v5': 'yolov5nu.pt',
            'v8': 'yolov8n.pt',
            'v11': 'yolo11n.pt',
        }
        return model_map.get(version.lower(), 'yolo11n.pt')


class YOLOInference:
    """
    YOLO 推論引擎
    """

    def __init__(self, model_path: str):
        """
        初始化推論引擎

        Args:
            model_path: 模型檔案路徑 (.pt 或 .onnx)
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型檔案不存在: {model_path}")

        self.model = YOLO(model_path)
        logger.info(f"載入模型: {model_path}")

    def predict(
        self,
        source,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        use_gray: bool = False
    ) -> list:
        """
        執行推論

        Args:
            source: 圖片路徑、資料夾或 numpy array
            conf_threshold: 信心度閾值
            iou_threshold: IOU 閾值
            use_gray: 是否使用灰階模式

        Returns:
            list: 偵測結果列表
        """
        # 處理灰階模式
        if use_gray and isinstance(source, str):
            import cv2
            img = cv2.imread(source, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                source = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # 執行推論
        results = self.model.predict(
            source,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False
        )

        # 格式化結果
        formatted_results = []
        for result in results:
            boxes = result.boxes
            detections = []

            for box in boxes:
                coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # 取得類別名稱
                if hasattr(self.model, 'names') and self.model.names:
                    cls_name = self.model.names[cls_id]
                else:
                    cls_name = str(cls_id)

                detections.append({
                    'class_id': cls_id,
                    'class_name': cls_name,
                    'confidence': conf,
                    'bbox': {
                        'x1': coords[0],
                        'y1': coords[1],
                        'x2': coords[2],
                        'y2': coords[3]
                    }
                })

            formatted_results.append({
                'detections': detections,
                'detection_count': len(detections)
            })

        return formatted_results

    def predict_batch(
        self,
        image_folder: str,
        conf_threshold: float = 0.25,
        use_gray: bool = False
    ) -> list:
        """
        批次推論資料夾中的圖片

        Args:
            image_folder: 圖片資料夾路徑
            conf_threshold: 信心度閾值
            use_gray: 是否使用灰階模式

        Returns:
            list: 每張圖片的偵測結果
        """
        valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        image_paths = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if os.path.splitext(f)[1].lower() in valid_exts
        ]

        results = []
        for img_path in image_paths:
            result = self.predict(img_path, conf_threshold, use_gray=use_gray)
            results.append({
                'image_path': img_path,
                'result': result[0] if result else {'detections': [], 'detection_count': 0}
            })

        return results

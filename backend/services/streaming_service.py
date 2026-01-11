"""
串流服務業務邏輯層
負責攝影機串流與即時偵測
"""

import cv2
import logging
import asyncio
from typing import Optional, Dict, Any
import base64
import numpy as np
from datetime import datetime

from engines.yolo_trainer import YOLOInference

logger = logging.getLogger(__name__)


class StreamingService:
    """串流服務類別"""

    def __init__(self):
        """初始化串流服務"""
        self.is_streaming = False
        self.camera = None
        self.model = None
        self.camera_id = 0
        self.conf_threshold = 0.25
        self.iou_threshold = 0.45
        self.use_gray = False

    def load_model(self, model_path: str) -> bool:
        """
        載入 YOLO 模型

        Args:
            model_path: 模型檔案路徑

        Returns:
            bool: 是否成功載入
        """
        try:
            self.model = YOLOInference(model_path)
            logger.info(f"✅ 模型已載入: {model_path}")
            return True
        except Exception as e:
            logger.error(f"載入模型失敗: {e}", exc_info=True)
            return False

    def start_camera(self, camera_id: int = 0) -> bool:
        """
        啟動攝影機

        Args:
            camera_id: 攝影機 ID（預設 0）

        Returns:
            bool: 是否成功啟動
        """
        try:
            self.camera = cv2.VideoCapture(camera_id)

            if not self.camera.isOpened():
                logger.error(f"無法開啟攝影機: {camera_id}")
                return False

            self.camera_id = camera_id
            self.is_streaming = True

            logger.info(f"✅ 攝影機已啟動: {camera_id}")
            return True

        except Exception as e:
            logger.error(f"啟動攝影機失敗: {e}", exc_info=True)
            return False

    def stop_camera(self):
        """停止攝影機"""
        self.is_streaming = False

        if self.camera:
            self.camera.release()
            self.camera = None
            logger.info("✅ 攝影機已停止")

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        捕捉一幀畫面

        Returns:
            Optional[np.ndarray]: 畫面或 None
        """
        if not self.camera or not self.is_streaming:
            return None

        ret, frame = self.camera.read()

        if not ret:
            logger.warning("無法讀取攝影機畫面")
            return None

        return frame

    def detect_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        對畫面進行物件偵測

        Args:
            frame: 畫面

        Returns:
            Dict[str, Any]: 偵測結果
        """
        if self.model is None:
            return {
                'detections': [],
                'detection_count': 0,
                'error': '模型未載入'
            }

        try:
            # 執行推論
            results = self.model.predict(
                frame,
                conf_threshold=self.conf_threshold,
                iou_threshold=self.iou_threshold,
                use_gray=self.use_gray
            )

            return results[0] if results else {
                'detections': [],
                'detection_count': 0
            }

        except Exception as e:
            logger.error(f"偵測失敗: {e}", exc_info=True)
            return {
                'detections': [],
                'detection_count': 0,
                'error': str(e)
            }

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: list
    ) -> np.ndarray:
        """
        在畫面上繪製偵測結果

        Args:
            frame: 原始畫面
            detections: 偵測結果列表

        Returns:
            np.ndarray: 繪製後的畫面
        """
        annotated_frame = frame.copy()

        for detection in detections:
            bbox = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']

            # 座標
            x1 = int(bbox['x1'])
            y1 = int(bbox['y1'])
            x2 = int(bbox['x2'])
            y2 = int(bbox['y2'])

            # 繪製邊界框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 繪製標籤
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            # 背景矩形
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                (0, 255, 0),
                -1
            )

            # 文字
            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )

        return annotated_frame

    def frame_to_base64(self, frame: np.ndarray) -> str:
        """
        將畫面轉為 Base64 字串

        Args:
            frame: 畫面

        Returns:
            str: Base64 編碼的 JPEG 圖片
        """
        try:
            # 編碼為 JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

            # 轉為 Base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')

            return f"data:image/jpeg;base64,{jpg_as_text}"

        except Exception as e:
            logger.error(f"畫面編碼失敗: {e}")
            return ""

    async def stream_generator(self):
        """
        串流生成器（異步）

        Yields:
            Dict[str, Any]: 每一幀的偵測結果與畫面
        """
        while self.is_streaming:
            # 捕捉畫面
            frame = self.capture_frame()

            if frame is None:
                await asyncio.sleep(0.1)
                continue

            # 偵測物件
            detection_result = self.detect_frame(frame)

            # 繪製偵測結果
            annotated_frame = self.draw_detections(
                frame,
                detection_result.get('detections', [])
            )

            # 轉為 Base64
            frame_base64 = self.frame_to_base64(annotated_frame)

            # 產生結果
            yield {
                'timestamp': datetime.now().isoformat(),
                'frame': frame_base64,
                'detections': detection_result.get('detections', []),
                'detection_count': detection_result.get('detection_count', 0),
                'error': detection_result.get('error')
            }

            # 控制 FPS（約 30 FPS）
            await asyncio.sleep(0.033)

    def get_status(self) -> Dict[str, Any]:
        """
        取得串流狀態

        Returns:
            Dict[str, Any]: 狀態資訊
        """
        return {
            'is_streaming': self.is_streaming,
            'camera_id': self.camera_id,
            'model_loaded': self.model is not None,
            'conf_threshold': self.conf_threshold,
            'iou_threshold': self.iou_threshold,
            'use_gray': self.use_gray
        }

    def update_config(
        self,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        use_gray: Optional[bool] = None
    ):
        """
        更新偵測配置

        Args:
            conf_threshold: 信心度閾值
            iou_threshold: IOU 閾值
            use_gray: 是否使用灰階
        """
        if conf_threshold is not None:
            self.conf_threshold = conf_threshold
        if iou_threshold is not None:
            self.iou_threshold = iou_threshold
        if use_gray is not None:
            self.use_gray = use_gray

        logger.info(f"偵測配置已更新: conf={self.conf_threshold}, iou={self.iou_threshold}, gray={self.use_gray}")


# 全域串流服務實例
_streaming_service = None


def get_streaming_service() -> StreamingService:
    """取得串流服務單例"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service

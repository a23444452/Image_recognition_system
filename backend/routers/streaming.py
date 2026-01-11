"""
串流偵測 API Router
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import logging
import asyncio

from services.streaming_service import get_streaming_service
from schemas.streaming import (
    StreamingConfig,
    StreamingUpdateConfig,
    StreamingStatus
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/start", response_model=StreamingStatus)
async def start_streaming(config: StreamingConfig):
    """
    啟動串流偵測

    Args:
        config: 串流配置

    Returns:
        StreamingStatus: 串流狀態
    """
    service = get_streaming_service()

    try:
        # 檢查是否已在串流
        if service.is_streaming:
            raise HTTPException(status_code=400, detail="串流已在運行中")

        # 載入模型
        if not service.load_model(config.model_path):
            raise HTTPException(status_code=400, detail="模型載入失敗")

        # 更新配置
        service.update_config(
            conf_threshold=config.conf_threshold,
            iou_threshold=config.iou_threshold,
            use_gray=config.use_gray
        )

        # 啟動攝影機
        if not service.start_camera(config.camera_id):
            raise HTTPException(status_code=400, detail="攝影機啟動失敗")

        logger.info(f"✅ 串流已啟動: camera={config.camera_id}, model={config.model_path}")

        return service.get_status()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟動串流失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"啟動串流失敗: {str(e)}")


@router.post("/stop")
async def stop_streaming():
    """
    停止串流偵測

    Returns:
        dict: 操作結果
    """
    service = get_streaming_service()

    try:
        if not service.is_streaming:
            raise HTTPException(status_code=400, detail="串流未運行")

        service.stop_camera()

        logger.info("✅ 串流已停止")

        return {
            "message": "串流已停止",
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止串流失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止串流失敗: {str(e)}")


@router.get("/status", response_model=StreamingStatus)
async def get_streaming_status():
    """
    取得串流狀態

    Returns:
        StreamingStatus: 串流狀態
    """
    service = get_streaming_service()
    return service.get_status()


@router.patch("/config", response_model=StreamingStatus)
async def update_streaming_config(config: StreamingUpdateConfig):
    """
    更新串流配置

    Args:
        config: 更新配置

    Returns:
        StreamingStatus: 更新後的狀態
    """
    service = get_streaming_service()

    try:
        service.update_config(
            conf_threshold=config.conf_threshold,
            iou_threshold=config.iou_threshold,
            use_gray=config.use_gray
        )

        logger.info("✅ 串流配置已更新")

        return service.get_status()

    except Exception as e:
        logger.error(f"更新配置失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")


@router.websocket("/ws")
async def websocket_streaming(websocket: WebSocket):
    """
    串流 WebSocket 端點

    即時推送偵測結果與畫面

    Args:
        websocket: WebSocket 連線
    """
    service = get_streaming_service()

    await websocket.accept()

    try:
        # 發送連線成功訊息
        await websocket.send_json({
            "type": "connected",
            "message": "已連線到串流"
        })

        # 檢查是否正在串流
        if not service.is_streaming:
            await websocket.send_json({
                "type": "error",
                "message": "串流未啟動，請先啟動串流"
            })
            await websocket.close()
            return

        # 串流循環
        async for frame_data in service.stream_generator():
            try:
                # 推送畫面與偵測結果
                await websocket.send_json({
                    "type": "frame",
                    "data": frame_data
                })

                # 檢查是否還在串流
                if not service.is_streaming:
                    await websocket.send_json({
                        "type": "stopped",
                        "message": "串流已停止"
                    })
                    break

            except WebSocketDisconnect:
                logger.info("WebSocket 客戶端斷線")
                break

            except Exception as e:
                logger.error(f"推送畫面失敗: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"推送畫面失敗: {str(e)}"
                })
                break

    except WebSocketDisconnect:
        logger.info("WebSocket 客戶端主動斷線")

    except Exception as e:
        logger.error(f"WebSocket 錯誤: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"串流錯誤: {str(e)}"
            })
        except:
            pass

    finally:
        try:
            await websocket.close()
        except:
            pass

# 系統架構文檔 (ARCHITECTURE.md)

## 📋 目錄

1. [系統概述](#系統概述)
2. [架構設計](#架構設計)
3. [技術棧](#技術棧)
4. [核心模組](#核心模組)
5. [資料流程](#資料流程)
6. [關鍵設計決策](#關鍵設計決策)
7. [安全性考量](#安全性考量)
8. [效能優化](#效能優化)
9. [擴展性設計](#擴展性設計)

---

## 系統概述

**YOLO 全端影像辨識系統** 是一個基於微服務架構的完整物件偵測平台，整合了資料集管理、模型訓練、即時推論與串流偵測功能。

### 核心特性

- **全端整合**：前後端分離的現代化 Web 應用架構
- **非同步處理**：基於任務隊列的背景訓練機制
- **即時通訊**：WebSocket 雙向串流推送
- **模組化設計**：Router → Service → Engine 三層架構
- **容器化部署**：Docker Compose 一鍵部署

---

## 架構設計

### 整體架構圖

```
┌────────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                            │
│                     http://localhost:5173                           │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                    HTTP + WebSocket
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                    Frontend (React + Vite)                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Components: TrainingForm, TrainingMonitor, DatasetManager   │  │
│  │  Pages: TrainingPage, DatasetsPage, ModelsPage, StreamingPage│  │
│  │  Router: React Router (客戶端路由)                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                    REST API + WebSocket
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│               Backend Gateway (FastAPI - Port 8000)                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Routers (API Endpoints)                                      │  │
│  │  ├── /api/v1/training     (訓練任務管理)                      │  │
│  │  ├── /api/v1/datasets     (資料集 CRUD)                       │  │
│  │  ├── /api/v1/models       (模型管理)                          │  │
│  │  ├── /api/v1/streaming    (串流控制)                          │  │
│  │  └── /ws                  (WebSocket 端點)                    │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Services (業務邏輯層)                                         │  │
│  │  ├── TrainingService      (訓練任務協調)                      │  │
│  │  ├── DatasetService       (資料集驗證與處理)                  │  │
│  │  ├── ModelService         (模型註冊與切換)                    │  │
│  │  └── StreamingService     (串流推論管理)                      │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Engines (核心引擎)                                            │  │
│  │  └── YOLOTrainer          (YOLO 訓練引擎)                     │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Models (資料庫模型 - SQLAlchemy ORM)                         │  │
│  │  ├── TrainingTask         (訓練任務記錄)                      │  │
│  │  ├── Dataset              (資料集元資料)                      │  │
│  │  └── Model                (模型註冊資訊)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────┬──────────────┬──────────────┬─────────────────────────┘
             │              │              │
             ▼              ▼              ▼
   ┌─────────────┐  ┌──────────┐  ┌────────────────┐
   │   SQLite    │  │  Redis   │  │ File Storage   │
   │  (Metadata) │  │ (Queue)  │  │ (Models/Data)  │
   └─────────────┘  └────┬─────┘  └────────────────┘
                         │
                    ┌────▼────┐
                    │RQ Worker│ (Background Training)
                    │  Pool   │
                    └─────────┘
```

### 分層架構說明

#### 1. **前端層 (Presentation Layer)**
- **框架**: React 18 + Vite
- **責任**: UI 渲染、用戶交互、狀態管理
- **通訊**:
  - REST API：CRUD 操作、配置提交
  - WebSocket：訓練進度、串流畫面即時推送

#### 2. **API 層 (API Gateway Layer)**
- **框架**: FastAPI
- **責任**: 請求路由、參數驗證、CORS 處理
- **模式**: Router 模式（按功能模組拆分路由）

#### 3. **服務層 (Business Logic Layer)**
- **責任**: 業務邏輯編排、資料驗證、錯誤處理
- **特點**:
  - 與資料庫 ORM 交互
  - 調用底層引擎執行核心任務
  - 發布任務到 RQ 隊列

#### 4. **引擎層 (Engine Layer)**
- **責任**: 核心 AI 功能實現（訓練、推論）
- **特點**:
  - 封裝 Ultralytics YOLO API
  - 提供訓練進度回調機制
  - 獨立於業務邏輯

#### 5. **資料層 (Data Layer)**
- **SQLite**: 結構化資料持久化（任務、資料集、模型元資料）
- **Redis**: 任務隊列、快取
- **File System**: 模型權重、資料集檔案

---

## 技術棧

### Backend

| 類別           | 技術                          | 版本       | 用途                        |
|----------------|-------------------------------|------------|-----------------------------|
| **Web 框架**   | FastAPI                       | 0.104.1    | REST API + WebSocket        |
| **ASGI Server**| Uvicorn                       | 0.24.0     | 高效能非同步伺服器          |
| **任務隊列**   | Python-RQ                     | 1.15.1     | 背景訓練任務處理            |
| **快取/隊列**  | Redis                         | 5.0.1      | 任務隊列 + 快取             |
| **AI 框架**    | Ultralytics YOLO              | 8.0.0+     | YOLOv5/v8/v11 訓練與推論    |
| **深度學習**   | PyTorch                       | 2.0.0+     | 神經網路訓練                |
| **影像處理**   | OpenCV                        | 4.8.1      | 圖片讀取與預處理            |
| **ORM**        | SQLAlchemy                    | 2.0.23     | 資料庫 ORM                  |
| **資料驗證**   | Pydantic                      | 2.5.0      | 請求/回應資料驗證           |

### Frontend

| 類別           | 技術                          | 版本       | 用途                        |
|----------------|-------------------------------|------------|-----------------------------|
| **框架**       | React                         | 18.x       | UI 框架                     |
| **建構工具**   | Vite                          | 5.x        | 快速開發伺服器 + 打包       |
| **路由**       | React Router                  | 6.x        | 客戶端路由                  |
| **樣式**       | Tailwind CSS                  | 3.x        | Utility-first CSS 框架      |
| **表單管理**   | React Hook Form               | 7.x        | 高效能表單處理              |
| **圖表**       | Recharts                      | 2.x        | 訓練指標視覺化              |
| **圖示**       | Lucide React                  | 0.x        | 現代化圖示庫                |

### Infrastructure

| 類別           | 技術                          | 用途                        |
|----------------|-------------------------------|-----------------------------|
| **容器化**     | Docker + Docker Compose       | 服務編排與部署              |
| **CI/CD**      | GitHub Actions                | 自動化測試與部署            |
| **監控**       | Prometheus (規劃中)           | 系統指標收集                |
| **日誌**       | Python logging                | 應用層日誌記錄              |

---

## 核心模組

### 1. 訓練模組 (Training Module)

**位置**: `backend/routers/training.py` + `backend/services/training_service.py`

**功能**:
- 接收訓練配置 (模型版本、超參數、資料集)
- 創建訓練任務並儲存至資料庫
- 發布任務至 RQ 隊列
- 透過 WebSocket 推送訓練進度

**流程圖**:
```
用戶提交配置
    ↓
TrainingService 驗證參數
    ↓
創建 TrainingTask (status=pending)
    ↓
發布到 RQ 隊列 (rq worker training)
    ↓
Worker 拉取任務 → YOLOTrainer.train()
    ↓
每個 Epoch 回調 → 更新資料庫 → WebSocket 推送
    ↓
訓練完成 → status=completed + 儲存 best.pt
```

**關鍵類別**:
- `TrainingService`: 任務協調、資料庫操作
- `YOLOTrainer`: YOLO 訓練引擎
- `TrainingTask` (ORM): 任務元資料

---

### 2. 資料集管理模組 (Dataset Module)

**位置**: `backend/routers/datasets.py` + `backend/services/dataset_service.py`

**功能**:
- 建立資料集 (自動分割 train/val)
- 驗證目錄結構 (images/ + labels/)
- 生成 `data.yaml` 配置檔
- 統計資訊 (圖片數量、類別分佈)
- 樣本圖片預覽

**資料集結構驗證**:
```
dataset_name/
├── train/
│   ├── images/       # 訓練圖片 (.jpg, .png)
│   └── labels/       # YOLO 標註 (.txt)
└── val/
    ├── images/       # 驗證圖片
    └── labels/       # 驗證標註
```

**關鍵功能**:
- `ProcessPoolExecutor`: 並行處理檔案檢查
- YAML 動態生成: 自動偵測類別名稱

---

### 3. 模型管理模組 (Model Module)

**位置**: `backend/routers/models.py` + `backend/services/model_service.py`

**功能**:
- 註冊訓練完成的模型 (儲存指標: mAP, Precision, Recall)
- 啟用/停用模型 (單一活躍模型機制)
- 模型比較 (多模型指標對比)
- 統計儀表板 (模型數量、版本分佈)

**資料模型**:
```python
class Model(Base):
    id: str (UUID)
    name: str
    version: str
    model_path: str (檔案系統路徑)
    yolo_version: str (v5/v8/v11)
    is_active: bool (僅一個模型可為 True)
    metrics: JSON (mAP@0.5, mAP@0.5:0.95, Precision, Recall)
    created_at: DateTime
```

---

### 4. 即時串流模組 (Streaming Module)

**位置**: `backend/routers/streaming.py` + `backend/services/streaming_service.py`

**功能**:
- 啟動/停止攝影機串流
- YOLO 即時推論 (約 30 FPS)
- 動態調整偵測參數 (信心度、IOU 閾值)
- WebSocket 推送畫面 (Base64 JPEG)

**串流架構**:
```
OpenCV 攝影機 → YOLO 推論 → 繪製邊界框
    ↓
JPEG 編碼 (品質 80) → Base64 編碼
    ↓
WebSocket 推送 → 前端 Canvas 渲染
```

**效能控制**:
- FPS 控制: 限制推送頻率約 30 FPS
- 畫面品質: JPEG 品質 80 (平衡速度與清晰度)
- 灰階模式: 可選啟用以提升效能

---

## 資料流程

### 訓練任務資料流

```
┌─────────────┐
│ 前端表單提交 │
└──────┬──────┘
       │ POST /api/v1/training/start
       ▼
┌─────────────────┐
│  TrainingRouter │ (參數驗證)
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ TrainingService  │ (創建任務 → 發布至 RQ)
└──────┬───────────┘
       │
       ▼
┌──────────────┐       ┌─────────────┐
│ Redis Queue  │──────>│  RQ Worker  │
└──────────────┘       └──────┬──────┘
                              │
                              ▼
                       ┌───────────────┐
                       │  YOLOTrainer  │ (執行訓練)
                       └──────┬────────┘
                              │
           每個 Epoch 回調 ───┤
                              │
                              ▼
                       ┌────────────────┐
                       │ Update Database│ (更新進度)
                       └──────┬─────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ WebSocket Broadcast│ → 前端即時顯示
                       └─────────────────┘
```

### WebSocket 通訊流程

```
前端 WebSocket 連線 → /ws/training/{task_id}
    ↓
後端接受連線 → 註冊到 active_connections
    ↓
訓練進度更新時 → broadcast_progress()
    ↓
推送 JSON 訊息:
{
  "type": "progress",
  "epoch": 10,
  "total_epochs": 100,
  "metrics": {"loss": 0.5, "mAP@0.5": 0.85}
}
    ↓
前端接收 → 更新 UI (進度條、圖表)
```

---

## 關鍵設計決策

### 1. 任務隊列架構 (RQ vs Celery)

**選擇**: Python-RQ
**原因**:
- ✅ 輕量級，配置簡單（僅需 Redis）
- ✅ 原生 Python 函數支援（無需序列化複雜度）
- ✅ 適合中小規模訓練任務
- ❌ 功能較 Celery 少（無定時任務、無優先級隊列）

**權衡**: 本專案訓練任務為低頻、長時間操作，RQ 已足夠。

---

### 2. WebSocket 節流機制

**問題**: 訓練每秒產生大量進度更新，WebSocket 推送過於頻繁。

**解決方案**:
- 0.5 秒輪詢機制（前端定時請求最新進度）
- 避免每次資料庫更新都推送

**實作**:
```python
# backend/routers/websocket.py
async def poll_training_progress(task_id: str):
    while True:
        task = get_task_from_db(task_id)
        await websocket.send_json(task.progress)
        await asyncio.sleep(0.5)  # 0.5 秒輪詢
```

---

### 3. 單一活躍模型機制

**設計**: 同時只能有一個模型處於 `is_active=True` 狀態。

**原因**:
- 串流模組需明確知道使用哪個模型
- 避免模型切換混亂

**實作**:
```python
def activate_model(model_id: str):
    # 停用所有模型
    db.query(Model).update({"is_active": False})
    # 啟用指定模型
    model = db.query(Model).filter_by(id=model_id).first()
    model.is_active = True
    db.commit()
```

---

### 4. 前後端分離 CORS 配置

**問題**: 前端 (localhost:5173) 無法直接訪問後端 (localhost:8000)。

**解決方案**:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**生產環境注意**: 需改為白名單域名。

---

### 5. 並行處理資料集驗證

**挑戰**: 驗證數千張圖片的標註檔格式耗時長。

**解決方案**:
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as executor:
    results = executor.map(validate_label_file, label_files)
```

**效能提升**: 4 核心 CPU 約 3-4x 速度提升。

---

## 安全性考量

### 1. 輸入驗證
- **Pydantic Models**: 所有 API 請求使用 Pydantic 自動驗證
- **檔案路徑驗證**: 防止路徑穿越攻擊
- **檔案大小限制**: 限制上傳檔案大小

### 2. 認證與授權 (規劃中)
- **JWT Token**: 使用者認證
- **RBAC**: 角色基礎存取控制
- **API Key**: 第三方 API 整合

### 3. 資料保護
- **環境變數**: 敏感資訊存放於 `.env`
- **SQLite 檔案權限**: 限制讀寫權限
- **模型檔案存取**: 僅後端可存取模型目錄

### 4. CORS 安全
- **生產環境**: 僅允許特定域名
- **開發環境**: 允許 localhost

---

## 效能優化

### 1. 訓練效能
- **GPU 加速**: 自動偵測 CUDA/MPS
- **批次大小調整**: 根據 GPU 記憶體動態調整
- **混合精度訓練**: AMP (Automatic Mixed Precision)

### 2. 串流效能
- **JPEG 編碼**: 品質 80 平衡清晰度與速度
- **Base64 編碼**: 避免二進位傳輸問題
- **FPS 控制**: 限制約 30 FPS 避免過載
- **灰階模式**: 可選啟用以提升推論速度

### 3. 資料庫效能
- **索引**: 為常查詢欄位建立索引 (task_id, is_active)
- **連線池**: SQLAlchemy 連線池管理
- **批次操作**: 批次插入/更新減少 I/O

### 4. 前端效能
- **React.memo**: 避免不必要的重新渲染
- **虛擬化列表**: 大量資料使用虛擬滾動
- **懶載入**: 圖片懶載入

---

## 擴展性設計

### 水平擴展

#### 1. RQ Worker 擴展
```bash
# 啟動多個 Worker
rq worker training &
rq worker training &
rq worker training &
```

**負載平衡**: Redis 自動分配任務。

#### 2. FastAPI 多實例
```bash
# 使用多 worker
uvicorn main:app --workers 4
```

**注意**: WebSocket 需考慮狀態同步（可用 Redis Pub/Sub）。

---

### 垂直擴展

#### 1. 資料庫遷移至 PostgreSQL
```python
# config/database.py
DATABASE_URL = "postgresql://user:pass@localhost/yolo_db"
```

**優勢**: 更好的並發、JSONB 支援、全文檢索。

#### 2. Redis Cluster
- 分散式快取
- 高可用性

---

### 功能擴展

#### 1. 多使用者系統
- 加入 User 資料表
- 資料集/模型加入 user_id 外鍵
- JWT 認證

#### 2. 分散式訓練
- 整合 PyTorch DDP (Distributed Data Parallel)
- 多 GPU 訓練

#### 3. 模型版本控制
- 整合 MLflow 或 DVC
- 實驗追蹤與模型註冊

---

## 系統限制與已知問題

### 限制

1. **單一活躍模型**: 同時只能使用一個模型進行串流偵測
2. **無歷史記錄**: 訓練記錄僅保存元資料，無訓練日誌歸檔
3. **無認證系統**: 目前無使用者登入功能
4. **SQLite 並發限制**: 高並發情況下可能鎖表

### 已知問題

1. **訓練中斷處理**: Worker 異常退出時任務狀態不更新
2. **WebSocket 斷線重連**: 前端需手動刷新頁面
3. **大檔案上傳**: 無分片上傳機制

---

## 未來規劃

- [ ] 整合 Prometheus + Grafana 監控
- [ ] 加入使用者認證與權限管理
- [ ] 支援分散式訓練 (Multi-GPU)
- [ ] 模型量化與優化 (ONNX, TensorRT)
- [ ] 訓練歷史視覺化 (TensorBoard 整合)
- [ ] RESTful API 完整文檔 (OpenAPI 3.0)
- [ ] 自動化測試覆蓋率提升至 80%+

---

## 參考資源

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Ultralytics YOLO 文檔](https://docs.ultralytics.com/)
- [Python-RQ 文檔](https://python-rq.org/)
- [React 官方文檔](https://react.dev/)
- [Tailwind CSS 文檔](https://tailwindcss.com/)

---

**最後更新**: 2026-01-12
**版本**: 1.0.0

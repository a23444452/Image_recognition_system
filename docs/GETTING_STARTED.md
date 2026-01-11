# 快速開始指南

本指南將幫助您快速設定並運行 YOLO 全端影像辨識系統。

## 📋 系統要求

### 必需
- **Python 3.10+** - 後端開發語言
- **Node.js 18+** - 前端開發環境
- **Redis 6+** - 任務隊列與快取
- **8GB+ RAM** - 建議記憶體
- **20GB+ 硬碟空間** - 用於模型與資料集

### 選用
- **GPU (NVIDIA CUDA / Apple MPS)** - 加速訓練與推論
- **Docker & Docker Compose** - 容器化部署
- **攝影機** - 用於即時串流偵測

## 🚀 快速安裝

### 方法一：自動化腳本（推薦）

```bash
# 1. Clone 專案
git clone https://github.com/a23444452/Image_recognition_system.git
cd Image_recognition_system

# 2. 執行安裝腳本（如果有提供）
./scripts/setup.sh

# 3. 啟動所有服務
./scripts/start.sh
```

### 方法二：手動安裝（詳細步驟）

#### 1️⃣ 後端設定

```bash
# 進入後端目錄
cd backend

# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 升級 pip
pip install --upgrade pip

# 安裝依賴
pip install -r requirements.txt

# (可選) 安裝效能優化套件
# pillow-simd 提供 4-6x 圖片處理效能提升
# 注意：在某些平台上可能需要編譯工具
pip install pillow-simd  # 如果安裝失敗，標準 Pillow 已足夠使用
```

**重要提示**：
- ✅ `requirements.txt` 已使用標準 `Pillow` 而非 `pillow-simd`
- ✅ 所有 Pydantic v2 相容性問題已修復
- ✅ 如果看到 `pillow-simd` 安裝失敗，這是正常的，系統會使用標準 Pillow

#### 2️⃣ 前端設定

```bash
# 進入前端目錄
cd frontend

# 安裝依賴
npm install

# (可選) 清除快取重新安裝
# npm cache clean --force
# rm -rf node_modules package-lock.json
# npm install
```

#### 3️⃣ Redis 安裝與啟動

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Windows (使用 WSL 或 Docker)
# 方式 1: WSL
wsl -d Ubuntu
sudo apt-get install redis-server
sudo service redis-server start

# 方式 2: Docker
docker run -d -p 6379:6379 redis:latest

# 檢查 Redis 狀態
redis-cli ping  # 應回應 PONG
```

## 🏃 啟動服務

### 開發環境（推薦）

需要開啟 **4 個終端視窗**，按順序執行：

#### 終端 1️⃣：Redis Server

```bash
# 方式 1: 前景執行（可看到日誌）
redis-server

# 方式 2: 背景服務（推薦）
brew services start redis  # macOS
# 或
sudo systemctl start redis  # Linux
```

#### 終端 2️⃣：RQ Worker（訓練任務處理）

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

rq worker training
```

**預期輸出**：
```
17:30:00 RQ worker 'rq:worker:...' started
17:30:00 Listening on queue: training
17:30:00 Worker started successfully
```

#### 終端 3️⃣：FastAPI 後端

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

uvicorn main:app --reload --reload-exclude 'venv/*' --host 0.0.0.0 --port 8000
```

**預期輸出**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
🚀 啟動應用程式...
✅ 資料庫初始化完成
✅ Redis 連線成功: localhost:6379
✅ 應用程式啟動完成
INFO:     Application startup complete.
```

**可能的警告（可忽略）**：
```
⚠️  Redis 連線失敗: Error...
⚠️  訓練功能將無法使用，請確認 Redis 服務運行中
```
→ 只要確認 Redis 正在運行即可

#### 終端 4️⃣：React 前端

```bash
cd frontend
npm run dev
```

**預期輸出**：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
  ➜  press h + enter to show help
```

### 使用 Docker Compose（適合生產環境）

```bash
# 啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f backend
docker-compose logs -f frontend

# 停止服務
docker-compose down

# 停止並刪除 volumes
docker-compose down -v
```

## ✅ 驗證安裝

### 1. 檢查前端
訪問：http://localhost:5173

您應該會看到：
- 🎯 YOLO 全端影像辨識系統
- 系統狀態顯示為「運行中」
- 功能卡片：訓練、即時偵測、資料集管理、模型管理

### 2. 檢查後端 API
訪問以下端點：

- **Swagger 文檔**: http://localhost:8000/docs
- **Redoc 文檔**: http://localhost:8000/redoc
- **健康檢查**: http://localhost:8000/
- **詳細健康檢查**: http://localhost:8000/health

使用 curl 測試：
```bash
# 基本健康檢查
curl http://localhost:8000/

# 預期回應：
# {"status":"healthy","message":"YOLO 全端影像辨識系統","version":"1.0.0"}

# 詳細健康檢查
curl http://localhost:8000/health

# 預期回應：
# {"status":"healthy","services":{"api":"running","redis":"pending","database":"pending"}}
```

### 3. 檢查 Redis
```bash
# 檢查 Redis 連線
redis-cli ping
# 應回應：PONG

# 檢查 Redis 資訊
redis-cli info server
```

### 4. 檢查 RQ Worker
```bash
# 查看佇列狀態
rq info

# 預期輸出會顯示：
# - Worker 數量
# - 待處理任務數
# - 已完成任務數
```

## 🎯 系統功能概覽

### Phase 1: 訓練系統 ✅
- **多步驟訓練配置**: 基本設定、訓練參數、資料集、進階選項
- **即時訓練監控**: WebSocket 推送進度、損失/mAP 圖表
- **背景任務佇列**: RQ + Redis 處理長時間訓練
- **任務管理**: 查詢、列表、刪除訓練任務

### Phase 2A: 資料集管理 ✅
- **資料集建立**: 自動分割 train/val (可調整比例)
- **統計資訊**: 圖片數量、類別分佈、資料集健康度
- **驗證功能**: 檢查目錄結構、標註檔格式
- **YAML 生成**: 自動產生 YOLO 訓練配置檔
- **樣本預覽**: 隨機顯示資料集圖片

### Phase 2B: 模型管理 ✅
- **模型註冊**: 記錄訓練指標 (mAP@0.5, mAP@0.5:0.95, Precision, Recall)
- **模型啟用**: 單一活躍模型系統
- **模型比較**: 多模型指標對比表格
- **統計儀表板**: 版本分佈、模型數量、平均指標
- **版本過濾**: 按 YOLO 版本 (v5/v8/v11) 篩選

### Phase 2C: 即時串流偵測 ✅
- **攝影機串流**: 支援多攝影機 (camera_id 選擇)
- **YOLO 即時偵測**: 整合 YOLOv5/v8/v11 推論引擎
- **動態配置**: 即時調整信心度、IOU 閾值、灰階模式
- **WebSocket 串流**: ~30 FPS 畫面推送 (Base64 JPEG)
- **偵測結果顯示**: 邊界框、類別、信心度即時呈現
- **即時統計**: FPS、偵測數量監控

## 📖 使用範例

### 完整工作流程

#### 1️⃣ 建立資料集
```bash
# 使用前端介面
1. 訪問 http://localhost:5173
2. 點擊「資料集管理」
3. 點擊「新增資料集」
4. 填寫資料集名稱和來源路徑
5. 調整 train/val 分割比例（預設 0.8）
6. 點擊「建立」

# 或使用 API
curl -X POST "http://localhost:8000/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_dataset",
    "source_folder": "/path/to/images",
    "split_ratio": 0.8
  }'
```

#### 2️⃣ 訓練模型
```bash
# 使用前端介面
1. 點擊「開始訓練」
2. 填寫多步驟表單：
   - 基本設定：任務名稱、模型類型、模型大小
   - 訓練參數：epochs, batch_size, img_size
   - 資料集：選擇已建立的資料集
   - 進階選項：學習率、優化器、資料增強
3. 點擊「開始訓練」
4. 即時監控訓練進度（WebSocket）

# 或使用 API
curl -X POST "http://localhost:8000/api/v1/training/start" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "my_training",
    "model_type": "yolov8",
    "model_size": "n",
    "dataset_id": "dataset_id_here",
    "epochs": 100,
    "batch_size": 16,
    "img_size": 640
  }'
```

#### 3️⃣ 註冊模型
```bash
# 使用前端介面
1. 訓練完成後，前往「模型管理」
2. 點擊「註冊新模型」
3. 填寫模型資訊和訓練指標
4. 點擊「註冊」
5. 點擊「啟用」設為活躍模型

# 或使用 API
curl -X POST "http://localhost:8000/api/v1/models" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_model",
    "version": "1.0.0",
    "model_path": "/path/to/best.pt",
    "yolo_version": "v8",
    "model_size": "n",
    "dataset_id": "dataset_id_here"
  }'
```

#### 4️⃣ 開始即時串流偵測
```bash
# 使用前端介面
1. 點擊「即時偵測」
2. 選擇模型（預設為活躍模型）
3. 設定攝影機 ID（預設 0）
4. 調整偵測參數（信心度、IOU 閾值）
5. 點擊「開始串流」
6. 即時查看偵測結果與畫面

# 或使用 API
curl -X POST "http://localhost:8000/api/v1/streaming/start" \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": 0,
    "model_path": "/path/to/best.pt",
    "conf_threshold": 0.25,
    "iou_threshold": 0.45,
    "use_gray": false
  }'

# 連接 WebSocket 接收即時畫面
# ws://localhost:8000/api/v1/streaming/ws
```

## 🔧 疑難排解

### 問題 1: pillow-simd 安裝失敗

**錯誤訊息**：
```
ERROR: No matching distribution found for pillow-simd==10.0.1.post0
```

**解決方案**：
```bash
# 已修復！requirements.txt 現在使用標準 Pillow
# 不需要任何額外操作，pillow-simd 是可選的效能優化

# 如果想要安裝 pillow-simd（可選）：
pip install pillow-simd
# 如果失敗，沒關係，標準 Pillow 功能完全相同
```

### 問題 2: Pydantic v2 警告

**警告訊息**：
```
UserWarning: Field "model_path" has conflict with protected namespace "model_".
```

**解決方案**：
```bash
# 已修復！所有 schema 已更新為 Pydantic v2 相容
# 不需要任何額外操作
```

### 問題 3: Redis 連線失敗

**錯誤訊息**：
```
⚠️  Redis 連線失敗: Error...
```

**解決方案**：
```bash
# 檢查 Redis 是否運行
redis-cli ping  # 應返回 PONG

# 啟動 Redis
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# 檢查 Redis 日誌
# macOS
tail -f /usr/local/var/log/redis.log

# Linux
sudo journalctl -u redis -f

# 重啟 Redis
redis-cli shutdown
redis-server --daemonize yes
```

### 問題 4: ImportError: cannot import name 'xxx'

**錯誤訊息**：
```
ImportError: cannot import name 'TrainingTaskResponse'
```

**解決方案**：
```bash
# 已修復！所有缺少的 schema 已補充
# 如果仍有問題，請：

# 1. 確認是最新版本
git pull origin main

# 2. 重新安裝依賴
pip install -r requirements.txt

# 3. 檢查是否在虛擬環境中
which python  # 應顯示 venv 路徑
```

### 問題 5: Python 依賴衝突

**解決方案**：
```bash
# 重建虛擬環境
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 問題 6: PyTorch/CUDA 問題

**錯誤訊息**：
```
RuntimeError: CUDA out of memory
# 或
RuntimeError: No CUDA GPUs are available
```

**解決方案**：
```bash
# CPU 版本（如果沒有 GPU）
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# GPU 版本（NVIDIA CUDA 11.8）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# GPU 版本（NVIDIA CUDA 12.1）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Apple Silicon (MPS)
# 已包含在 requirements.txt 中，無需額外安裝
```

### 問題 7: Node.js 依賴安裝失敗

**解決方案**：
```bash
# 清除快取重新安裝
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# 如果還是失敗，檢查 Node.js 版本
node -v  # 應該 >= 18.0.0
npm -v

# 升級 Node.js
# macOS
brew upgrade node

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 問題 8: 端口被佔用

**錯誤訊息**：
```
Error: Address already in use
OSError: [Errno 48] Address already in use
```

**解決方案**：
```bash
# 檢查端口使用情況
lsof -i :8000  # 後端 API
lsof -i :5173  # 前端 Vite
lsof -i :6379  # Redis

# 停止佔用端口的進程
kill -9 <PID>

# 或使用不同端口
# 後端
uvicorn main:app --reload --reload-exclude 'venv/*' --host 0.0.0.0 --port 8001

# 前端（修改 vite.config.js）
# server: { port: 5174 }
```

### 問題 9: 攝影機無法開啟

**錯誤訊息**：
```
無法開啟攝影機: 0
```

**解決方案**：
```bash
# 檢查可用的攝影機
python3 << EOF
import cv2
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i} is available")
        cap.release()
    else:
        break
EOF

# macOS：給予攝影機權限
# 系統偏好設定 → 安全性與隱私權 → 攝影機
# 確保允許 Terminal/iTerm 存取攝影機

# 測試攝影機
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Camera opened: {ret}")
if ret:
    print(f"Frame shape: {frame.shape}")
cap.release()
EOF
```

### 問題 10: 資料庫錯誤

**解決方案**：
```bash
# 重建資料庫
cd backend
rm -f database.db
python3 << EOF
from models.database import init_database
init_database()
print("✅ 資料庫重建完成")
EOF

# 或啟動 FastAPI 會自動初始化
uvicorn main:app --reload --reload-exclude 'venv/*'
```

## 📚 下一步

完成安裝後，您可以：

1. **閱讀系統架構**
   - [ARCHITECTURE.md](../ARCHITECTURE.md) - 了解系統設計

2. **API 文檔**
   - [README.md](../README.md) - 完整的 API 端點列表
   - http://localhost:8000/docs - 互動式 Swagger 文檔

3. **開發指南**
   - [DEVELOPMENT.md](./DEVELOPMENT.md) - 開發規範與最佳實踐

4. **部署指南**
   - [DEPLOYMENT.md](./DEPLOYMENT.md) - 生產環境部署

5. **開始使用**
   - 建立第一個資料集
   - 訓練第一個模型
   - 嘗試即時串流偵測

## 💡 實用提示

### 開發環境建議

1. **使用 tmux 或 screen 管理多個終端**
   ```bash
   # 安裝 tmux
   brew install tmux  # macOS
   sudo apt install tmux  # Linux

   # 創建 session
   tmux new -s yolo

   # 分割視窗
   Ctrl+b %  # 水平分割
   Ctrl+b "  # 垂直分割
   ```

2. **設定環境變數**
   ```bash
   # 建立 .env 檔案
   cd backend
   cat > .env << EOF
   REDIS_HOST=localhost
   REDIS_PORT=6379
   DATABASE_URL=sqlite:///./database.db
   EOF
   ```

3. **使用 VS Code 整合終端**
   - 開啟多個終端分頁
   - 使用 VS Code 的 tasks.json 自動啟動服務

4. **監控系統資源**
   ```bash
   # CPU/記憶體使用
   htop

   # GPU 使用（NVIDIA）
   watch -n 1 nvidia-smi

   # 磁碟空間
   df -h
   ```

### 效能優化建議

1. **訓練加速**
   - 使用 GPU 進行訓練
   - 調整 batch_size 以充分利用 GPU
   - 使用 mixed precision (FP16)

2. **推論加速**
   - 使用較小的模型 (n/s 而非 l/x)
   - 降低輸入影像解析度
   - 使用 TensorRT 優化（NVIDIA GPU）

3. **系統優化**
   - 使用 pillow-simd 替代標準 Pillow
   - 調整 Redis 記憶體配置
   - 使用 PostgreSQL 替代 SQLite（生產環境）

## 🆘 需要幫助？

- **GitHub Issues**: https://github.com/a23444452/Image_recognition_system/issues
- **文檔**: 查看 `/docs` 資料夾中的其他文件
- **API 文檔**: http://localhost:8000/docs

---

**祝您使用愉快！ 🎉**

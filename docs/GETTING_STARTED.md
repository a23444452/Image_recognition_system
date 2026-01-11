# 快速開始指南

## 系統要求

### 必需
- Python 3.10+
- Node.js 18+
- Redis 6+

### 選用
- GPU (NVIDIA CUDA / Apple MPS) - 用於加速訓練
- Docker & Docker Compose - 容器化部署

## 安裝步驟

### 方法一：使用自動化腳本（推薦）

```bash
# 1. Clone 專案
git clone https://github.com/a23444452/Image_recognition_system.git
cd Image_recognition_system

# 2. 執行安裝腳本
./scripts/setup.sh

# 3. 啟動所有服務
./scripts/start.sh
```

### 方法二：手動安裝

#### 後端設定

```bash
# 1. 建立虛擬環境
cd backend
python3 -m venv venv

# 2. 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 安裝依賴
pip install --upgrade pip
pip install -r requirements.txt
```

#### 前端設定

```bash
cd frontend
npm install
```

#### Redis 安裝

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# 檢查 Redis 狀態
redis-cli ping  # 應回應 PONG
```

## 啟動服務

### 開發環境

#### 終端 1：啟動 Redis
```bash
redis-server
```

#### 終端 2：啟動後端 API
```bash
cd backend
source venv/bin/activate
python main.py
```

#### 終端 3：啟動 RQ Worker
```bash
cd backend
source venv/bin/activate
rq worker training
```

#### 終端 4：啟動前端
```bash
cd frontend
npm run dev
```

### 使用 Docker Compose

```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

## 驗證安裝

1. 訪問前端：http://localhost:5173
2. 訪問 API 文檔：http://localhost:8000/docs
3. 檢查 API 健康狀態：
   ```bash
   curl http://localhost:8000/health
   ```

## 下一步

- 閱讀 [系統架構](../ARCHITECTURE.md)
- 查看 [API 文檔](http://localhost:8000/docs)
- 參考 [開發指南](./DEVELOPMENT.md)

## 常見問題

### Redis 連線失敗
```bash
# 檢查 Redis 是否運行
redis-cli ping

# 重啟 Redis
redis-server --daemonize yes
```

### Python 依賴安裝失敗
```bash
# 確保使用 pip 最新版本
pip install --upgrade pip

# 若 pillow-simd 安裝失敗，改用一般 pillow
pip install pillow
```

### Node.js 依賴安裝失敗
```bash
# 清除快取重新安裝
rm -rf node_modules package-lock.json
npm install
```

### 端口被佔用
```bash
# 檢查端口使用情況
lsof -i :8000  # 後端
lsof -i :5173  # 前端
lsof -i :6379  # Redis

# 停止佔用端口的進程
kill -9 <PID>
```

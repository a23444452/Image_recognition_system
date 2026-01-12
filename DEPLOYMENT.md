# 部署指南 (DEPLOYMENT.md)

## 📋 目錄

1. [部署概述](#部署概述)
2. [Docker 部署](#docker-部署)
3. [傳統部署](#傳統部署)
4. [雲端平台部署](#雲端平台部署)
5. [效能優化](#效能優化)
6. [監控與日誌](#監控與日誌)
7. [備份與還原](#備份與還原)
8. [疑難排解](#疑難排解)

---

## 部署概述

### 部署架構選擇

| 部署方式           | 優點                           | 缺點                     | 適用場景              |
|--------------------|--------------------------------|--------------------------|-----------------------|
| **Docker Compose** | 一鍵部署、環境隔離、易於擴展   | 需要 Docker 知識         | 小型生產環境、測試    |
| **傳統部署**       | 完全控制、無容器開銷           | 配置複雜、環境依賴多     | 特定硬體需求          |
| **Kubernetes**     | 高可用、自動擴展、負載平衡     | 學習曲線陡峭、資源需求高 | 大型生產環境          |
| **雲端平台**       | 託管服務、自動擴展、高可用性   | 成本較高                 | 快速上線、企業應用    |

---

## Docker 部署

### 前置需求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ 可用硬碟空間

### 安裝 Docker

#### macOS

```bash
# 使用 Homebrew
brew install --cask docker

# 或下載 Docker Desktop
# https://www.docker.com/products/docker-desktop/
```

#### Ubuntu/Debian

```bash
# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安裝 Docker Compose
sudo apt update
sudo apt install docker-compose-plugin

# 加入 Docker 群組（避免 sudo）
sudo usermod -aG docker $USER
newgrp docker
```

#### Windows

下載並安裝 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

---

### Docker Compose 部署（推薦）

#### 1. 準備環境變數

```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 檔案
nano .env
```

**生產環境必改項目**:
```bash
# 資料庫密碼（若使用 PostgreSQL）
DB_PASSWORD=your_secure_password_here

# Redis 密碼（生產環境建議設定）
REDIS_PASSWORD=your_redis_password

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 前端 API URL（改為實際域名）
VITE_API_URL=https://api.yourdomain.com
```

#### 2. 啟動所有服務

```bash
# 啟動所有容器（背景執行）
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 3. 驗證部署

```bash
# 檢查容器狀態
docker-compose ps

# 預期輸出：
# NAME                COMMAND                  SERVICE    STATUS
# backend             "uvicorn main:app ..."   backend    Up
# frontend            "npm run dev"            frontend   Up
# redis               "redis-server ..."       redis      Up
# worker              "rq worker training"     worker     Up
```

**測試 API**:
```bash
curl http://localhost:8000/health
```

**訪問前端**: 開啟瀏覽器訪問 http://localhost:5173

#### 4. 停止服務

```bash
# 停止容器（保留資料）
docker-compose stop

# 停止並移除容器（保留 volumes）
docker-compose down

# 停止並移除容器與 volumes（清空資料）
docker-compose down -v
```

---

### 自訂 Docker Compose 配置

#### 使用 PostgreSQL 替代 SQLite

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: yolo_db
      POSTGRES_USER: yolo_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U yolo_user"]
      interval: 10s
      timeout: 3s
      retries: 3

  backend:
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://yolo_user:${DB_PASSWORD}@db:5432/yolo_db

volumes:
  postgres_data:
```

#### 增加 RQ Worker 數量

```yaml
# docker-compose.yml
services:
  worker:
    # ... 其他配置 ...
    deploy:
      replicas: 4  # 啟動 4 個 Worker
```

#### 整合 Nginx 反向代理

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
```

**nginx.conf 範例**:
```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:5173;
}

server {
    listen 80;
    server_name yourdomain.com;

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://frontend;
    }
}
```

---

## 傳統部署

### 系統需求

- **作業系統**: Ubuntu 22.04 LTS / CentOS 8+ / macOS 12+
- **CPU**: 4 核心以上
- **RAM**: 16GB+
- **儲存**: 50GB+ SSD
- **GPU**: NVIDIA GPU with CUDA 11.8+ (選用，用於訓練加速)

---

### 後端部署

#### 1. 安裝系統依賴

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    redis-server \
    nginx \
    supervisor \
    libgl1-mesa-glx libglib2.0-0  # OpenCV 依賴
```

**CentOS/RHEL**:
```bash
sudo yum install -y \
    python311 python311-pip \
    redis \
    nginx \
    supervisor
```

#### 2. 建立專案目錄

```bash
# 建立應用目錄
sudo mkdir -p /var/www/yolo_system
sudo chown $USER:$USER /var/www/yolo_system

# Clone 專案
cd /var/www/yolo_system
git clone https://github.com/a23444452/Image_recognition_system.git .
```

#### 3. 設定後端

```bash
cd /var/www/yolo_system/backend

# 建立虛擬環境
python3.11 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install --upgrade pip
pip install -r requirements.txt

# 設定環境變數
cp ../.env.example ../.env
nano ../.env  # 編輯配置
```

#### 4. 設定 Systemd 服務（FastAPI）

建立服務檔案:
```bash
sudo nano /etc/systemd/system/yolo-api.service
```

**內容**:
```ini
[Unit]
Description=YOLO System FastAPI
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/yolo_system/backend
Environment="PATH=/var/www/yolo_system/backend/venv/bin"
ExecStart=/var/www/yolo_system/backend/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動服務:
```bash
sudo systemctl daemon-reload
sudo systemctl enable yolo-api
sudo systemctl start yolo-api
sudo systemctl status yolo-api
```

#### 5. 設定 Systemd 服務（RQ Worker）

建立服務檔案:
```bash
sudo nano /etc/systemd/system/yolo-worker@.service
```

**內容**:
```ini
[Unit]
Description=YOLO RQ Worker %i
After=network.target redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/yolo_system/backend
Environment="PATH=/var/www/yolo_system/backend/venv/bin"
ExecStart=/var/www/yolo_system/backend/venv/bin/rq worker training --url redis://localhost:6379/0

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動多個 Worker:
```bash
# 啟動 4 個 Worker
sudo systemctl enable yolo-worker@{1..4}.service
sudo systemctl start yolo-worker@{1..4}.service

# 檢查狀態
sudo systemctl status yolo-worker@1
```

---

### 前端部署

#### 1. 安裝 Node.js

```bash
# 使用 NodeSource 安裝最新 LTS 版本
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. 建構前端

```bash
cd /var/www/yolo_system/frontend

# 安裝依賴
npm install

# 設定環境變數
echo "VITE_API_URL=https://api.yourdomain.com" > .env.production

# 建構生產版本
npm run build
```

#### 3. 設定 Nginx

建立 Nginx 配置:
```bash
sudo nano /etc/nginx/sites-available/yolo-system
```

**內容**:
```nginx
# 前端配置
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /var/www/yolo_system/frontend/dist;
    index index.html;

    # 前端路由支援 (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 快取靜態資源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip 壓縮
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}

# 後端 API 配置
server {
    listen 80;
    server_name api.yourdomain.com;

    # API 端點
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 端點
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

啟用配置:
```bash
# 建立符號連結
sudo ln -s /etc/nginx/sites-available/yolo-system /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重新載入 Nginx
sudo systemctl reload nginx
```

#### 4. 設定 SSL (Let's Encrypt)

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 自動設定 SSL
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# 自動更新憑證
sudo systemctl enable certbot.timer
```

---

## 雲端平台部署

### AWS 部署

#### 架構圖

```
┌─────────────────────────────────────────────────┐
│               CloudFront (CDN)                   │
│           https://yourdomain.com                 │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────▼───────┐
        │  S3 Bucket   │ (前端靜態檔案)
        └──────────────┘
               │
        ┌──────▼───────────────────────────────┐
        │   Application Load Balancer (ALB)   │
        └──────┬───────────────────────────────┘
               │
        ┌──────▼──────┐
        │  ECS Fargate│ (FastAPI + Worker)
        │  Task x 2   │
        └──────┬──────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌─────────┐
│ RDS    │ │ElastiCache Redis │
│Postgres│ │        │ │  EFS    │
└────────┘ └────────┘ └─────────┘
```

#### 部署步驟

**1. 建立 ECR Repository**

```bash
# 建立 Docker 映像倉庫
aws ecr create-repository --repository-name yolo-backend
aws ecr create-repository --repository-name yolo-frontend

# 登入 ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# 建置並推送映像
docker build -t yolo-backend:latest ./backend
docker tag yolo-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/yolo-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/yolo-backend:latest
```

**2. 建立 ECS Cluster**

```bash
# 使用 AWS CLI 建立 Fargate Cluster
aws ecs create-cluster --cluster-name yolo-production
```

**3. 設定 RDS PostgreSQL**

```bash
# 使用 Terraform 或 CloudFormation 自動化建立
# 或在 AWS Console 手動建立
# - Engine: PostgreSQL 15
# - Instance Class: db.t3.medium
# - Storage: 100GB GP3
```

**4. 設定 ElastiCache Redis**

```bash
# 建立 Redis Cluster
# - Engine: Redis 7.0
# - Node Type: cache.t3.medium
# - Number of Nodes: 2 (Multi-AZ)
```

**5. 部署前端到 S3 + CloudFront**

```bash
# 建構前端
cd frontend
npm run build

# 上傳到 S3
aws s3 sync dist/ s3://yolo-frontend-bucket/ --delete

# 清除 CloudFront 快取
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

---

### Google Cloud Platform (GCP) 部署

#### 使用 Cloud Run

```bash
# 建構容器映像
gcloud builds submit --tag gcr.io/your-project/yolo-backend

# 部署到 Cloud Run
gcloud run deploy yolo-api \
  --image gcr.io/your-project/yolo-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

---

### Azure 部署

#### 使用 Azure Container Instances

```bash
# 建構並推送映像到 ACR
az acr build --registry yoloregistry --image yolo-backend:latest ./backend

# 部署容器
az container create \
  --resource-group yolo-rg \
  --name yolo-api \
  --image yoloregistry.azurecr.io/yolo-backend:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000
```

---

## 效能優化

### 後端優化

#### 1. Uvicorn Worker 數量調整

```bash
# 根據 CPU 核心數設定
uvicorn main:app --workers $(nproc)

# 或手動設定
uvicorn main:app --workers 8
```

#### 2. 啟用 Gunicorn

```bash
pip install gunicorn

# 使用 Gunicorn 管理 Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### 3. 資料庫連線池優化

```python
# backend/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 基本連線數
    max_overflow=10,       # 額外連線數
    pool_pre_ping=True,    # 健康檢查
    pool_recycle=3600      # 連線回收時間（秒）
)
```

#### 4. Redis 快取策略

```python
# 快取模型推論結果
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_model_prediction(image_hash):
    # 檢查快取
    cached = redis_client.get(f"prediction:{image_hash}")
    if cached:
        return json.loads(cached)

    # 執行推論
    result = model.predict(image)

    # 快取結果（5分鐘）
    redis_client.setex(f"prediction:{image_hash}", 300, json.dumps(result))
    return result
```

---

### 前端優化

#### 1. 程式碼分割

```jsx
// frontend/src/App.jsx
import { lazy, Suspense } from 'react';

const TrainingPage = lazy(() => import('./pages/TrainingPage'));
const StreamingPage = lazy(() => import('./pages/StreamingPage'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/training" element={<TrainingPage />} />
        <Route path="/streaming" element={<StreamingPage />} />
      </Routes>
    </Suspense>
  );
}
```

#### 2. 建構優化

```js
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['lucide-react'],
          'chart-vendor': ['recharts']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
};
```

---

## 監控與日誌

### Prometheus + Grafana

#### 1. 安裝 Prometheus

**docker-compose.monitoring.yml**:
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'yolo-api'
    static_configs:
      - targets: ['backend:8000']
```

#### 2. 加入 Prometheus Metrics

```python
# backend/main.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 定義指標
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

### 日誌管理

#### 1. 設定結構化日誌

```python
# backend/utils/logger.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        return json.dumps(log_obj)

# 使用
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

#### 2. 日誌輪替

```python
# backend/main.py
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## 備份與還原

### 資料庫備份

#### SQLite 備份

```bash
# 手動備份
cp backend/yolo.db backend/yolo.db.backup

# 設定定時備份（cron）
# 編輯 crontab
crontab -e

# 每天凌晨 2 點備份
0 2 * * * cp /var/www/yolo_system/backend/yolo.db /backup/yolo.db.$(date +\%Y\%m\%d)
```

#### PostgreSQL 備份

```bash
# 手動備份
pg_dump -U yolo_user -h localhost yolo_db > backup.sql

# 還原
psql -U yolo_user -h localhost yolo_db < backup.sql

# 設定定時備份
0 2 * * * pg_dump -U yolo_user yolo_db | gzip > /backup/yolo_db_$(date +\%Y\%m\%d).sql.gz
```

---

### 模型與資料集備份

```bash
# 備份到 S3
aws s3 sync /var/www/yolo_system/backend/models/ s3://yolo-backups/models/
aws s3 sync /var/www/yolo_system/backend/datasets/ s3://yolo-backups/datasets/

# 從 S3 還原
aws s3 sync s3://yolo-backups/models/ /var/www/yolo_system/backend/models/
```

---

## 疑難排解

### 常見問題

#### 1. 容器無法啟動

```bash
# 檢查容器日誌
docker-compose logs backend

# 檢查容器狀態
docker-compose ps

# 進入容器除錯
docker-compose exec backend bash
```

#### 2. 記憶體不足

```yaml
# docker-compose.yml - 限制記憶體使用
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 3. 訓練任務失敗

```bash
# 檢查 RQ Worker 日誌
docker-compose logs worker

# 檢查 Redis 隊列
redis-cli
> LRANGE rq:queue:training 0 -1
> LRANGE rq:queue:failed 0 -1
```

---

### 效能診斷

#### 1. 檢查 API 回應時間

```bash
# 使用 Apache Bench
ab -n 1000 -c 10 http://localhost:8000/

# 使用 wrk
wrk -t4 -c100 -d30s http://localhost:8000/
```

#### 2. 資料庫查詢優化

```sql
-- 檢查慢查詢（PostgreSQL）
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- 分析查詢計劃
EXPLAIN ANALYZE SELECT * FROM training_tasks WHERE status = 'running';
```

---

## 安全性檢查清單

部署前請確認：

- [ ] 變更所有預設密碼（資料庫、Redis、管理員帳號）
- [ ] 啟用 HTTPS（SSL/TLS）
- [ ] 設定防火牆規則（僅開放必要端口：80, 443）
- [ ] 啟用 CORS 白名單（移除 `allow_origins=["*"]`）
- [ ] 設定檔案上傳大小限制
- [ ] 關閉 FastAPI `/docs` 端點（生產環境）
- [ ] 啟用速率限制（Rate Limiting）
- [ ] 設定日誌監控與告警
- [ ] 定期備份資料庫與模型檔案
- [ ] 更新依賴套件至最新穩定版本

---

## 效能基準測試

### 預期效能指標（參考值）

| 指標                  | 開發環境           | 生產環境（4C8G）    |
|-----------------------|-------------------|---------------------|
| **API 回應時間**      | < 100ms           | < 50ms              |
| **訓練啟動時間**      | < 2s              | < 1s                |
| **串流 FPS**          | 20-25 FPS         | 28-30 FPS           |
| **並發 API 請求**     | 50 req/s          | 200+ req/s          |
| **資料庫查詢**        | < 50ms            | < 20ms              |

---

**最後更新**: 2026-01-12
**版本**: 1.0.0

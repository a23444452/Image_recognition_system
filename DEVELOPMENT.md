# 開發指南 (DEVELOPMENT.md)

## 📋 目錄

1. [開發環境設定](#開發環境設定)
2. [專案結構](#專案結構)
3. [開發工作流程](#開發工作流程)
4. [編碼規範](#編碼規範)
5. [測試指南](#測試指南)
6. [除錯技巧](#除錯技巧)
7. [常見問題](#常見問題)
8. [貢獻指南](#貢獻指南)

---

## 開發環境設定

### 系統需求

| 項目           | 最低需求              | 推薦配置              |
|----------------|-----------------------|-----------------------|
| **作業系統**   | macOS 10.15+ / Ubuntu 20.04+ / Windows 10+ | macOS 14+ / Ubuntu 22.04+ |
| **Python**     | 3.10+                 | 3.11+                 |
| **Node.js**    | 18.0+                 | 20.0+                 |
| **RAM**        | 8GB                   | 16GB+                 |
| **GPU**        | 選用 (CUDA 11.8+)     | NVIDIA RTX 3060+      |
| **硬碟空間**   | 10GB                  | 50GB+ (SSD)           |

---

### 快速開始

#### 1. Clone 專案

```bash
git clone https://github.com/a23444452/Image_recognition_system.git
cd Image_recognition_system
```

#### 2. 一鍵安裝（推薦）

```bash
./scripts/setup.sh
```

腳本會自動完成：
- ✅ 檢查 Python、Node.js、Redis 安裝狀態
- ✅ 建立 Python 虛擬環境 (`backend/venv`)
- ✅ 安裝後端依賴 (`requirements.txt`)
- ✅ 安裝前端依賴 (`npm install`)
- ✅ 建立環境變數檔案 (`.env`)
- ✅ 建立必要目錄 (`models/`, `datasets/`, `logs/`)

#### 3. 手動安裝（進階）

##### 後端設定

```bash
cd backend

# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 升級 pip
pip install --upgrade pip

# 安裝依賴
pip install -r requirements.txt

# 選用：安裝效能優化版 Pillow
pip install -r requirements-optional.txt
```

##### 前端設定

```bash
cd frontend

# 安裝依賴
npm install

# 或使用 yarn
yarn install
```

##### Redis 安裝

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# Windows
# 下載 Redis MSI 安裝包或使用 WSL
```

---

### 環境變數配置

複製範例檔案：
```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 資料庫配置
DATABASE_URL=sqlite:///./yolo.db  # 開發環境使用 SQLite

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 前端配置
VITE_API_URL=http://localhost:8000

# 日誌配置
LOG_LEVEL=INFO
```

---

### 啟動開發伺服器

#### 方法一：一鍵啟動（推薦）

```bash
./scripts/start.sh
```

自動啟動：
- Redis 服務
- FastAPI 後端 (http://localhost:8000)
- React 前端 (http://localhost:5173)

#### 方法二：分別啟動

**終端 1 - 後端 API**
```bash
cd backend
source venv/bin/activate
python main.py

# 或使用 uvicorn 指令
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**終端 2 - RQ Worker (訓練任務處理)**
```bash
cd backend
source venv/bin/activate
rq worker training
```

**終端 3 - 前端**
```bash
cd frontend
npm run dev
```

---

### 驗證環境

```bash
# 檢查 Redis 連線
redis-cli ping  # 應回傳 PONG

# 檢查後端 API
curl http://localhost:8000/
# 預期輸出: {"status":"healthy","message":"YOLO 全端影像辨識系統","version":"1.0.0"}

# 檢查前端
open http://localhost:5173
```

---

## 專案結構

### 完整目錄樹

```
Image_recognition_system/
├── backend/                        # 後端程式碼
│   ├── engines/                   # 核心引擎
│   │   └── yolo_trainer.py       # YOLO 訓練引擎
│   ├── models/                    # SQLAlchemy ORM 模型
│   │   ├── database.py           # 資料庫連線配置
│   │   ├── training.py           # TrainingTask 模型
│   │   ├── dataset.py            # Dataset 模型
│   │   └── model.py              # Model 模型
│   ├── routers/                   # API 路由
│   │   ├── training.py           # 訓練任務 API
│   │   ├── datasets.py           # 資料集管理 API
│   │   ├── models.py             # 模型管理 API
│   │   ├── streaming.py          # 串流偵測 API
│   │   └── websocket.py          # WebSocket 端點
│   ├── schemas/                   # Pydantic 驗證模型
│   │   ├── training.py           # 訓練請求/回應 Schema
│   │   ├── dataset.py            # 資料集 Schema
│   │   └── model.py              # 模型 Schema
│   ├── services/                  # 業務邏輯層
│   │   ├── training_service.py   # 訓練服務
│   │   ├── dataset_service.py    # 資料集服務
│   │   ├── model_service.py      # 模型服務
│   │   └── streaming_service.py  # 串流服務
│   ├── utils/                     # 工具函數
│   │   ├── logger.py             # 日誌工具
│   │   └── validators.py         # 資料驗證
│   ├── workers/                   # RQ Worker 配置
│   │   └── training_worker.py    # 訓練 Worker
│   ├── tests/                     # 測試程式碼
│   │   ├── test_training.py
│   │   ├── test_datasets.py
│   │   └── test_models.py
│   ├── main.py                    # FastAPI 主程式
│   ├── requirements.txt           # Python 依賴
│   ├── requirements-optional.txt  # 選用依賴
│   └── Dockerfile                 # Docker 映像檔
├── frontend/                       # 前端程式碼
│   ├── src/
│   │   ├── components/           # React 元件
│   │   │   ├── TrainingForm.jsx  # 訓練表單
│   │   │   └── TrainingMonitor.jsx # 訓練監控
│   │   ├── pages/                # 頁面元件
│   │   │   ├── TrainingPage.jsx  # 訓練頁
│   │   │   ├── DatasetsPage.jsx  # 資料集頁
│   │   │   ├── ModelsPage.jsx    # 模型頁
│   │   │   └── StreamingPage.jsx # 串流頁
│   │   ├── hooks/                # 自訂 Hooks
│   │   │   └── useWebSocket.js   # WebSocket Hook
│   │   ├── contexts/             # Context API
│   │   ├── utils/                # 工具函數
│   │   ├── App.jsx               # 主應用程式
│   │   └── main.jsx              # 入口檔案
│   ├── public/                    # 靜態資源
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── config/                         # 配置檔案
├── scripts/                        # 自動化腳本
│   ├── setup.sh                  # 環境安裝
│   ├── start.sh                  # 啟動服務
│   └── stop.sh                   # 停止服務
├── docs/                           # 文檔
│   ├── ARCHITECTURE.md           # 系統架構
│   ├── DEVELOPMENT.md            # 開發指南 (本文件)
│   └── DEPLOYMENT.md             # 部署指南
├── .github/                        # GitHub 配置
│   └── workflows/
│       └── ci.yml                # CI/CD 配置
├── docker-compose.yml             # Docker 編排
├── .env.example                   # 環境變數範例
├── .gitignore
└── README.md                      # 專案說明
```

---

## 開發工作流程

### 1. 功能開發流程

#### Step 1: 建立功能分支

```bash
git checkout -b feature/your-feature-name
```

#### Step 2: 開發功能

**後端 API 開發範例 - 新增端點**

```python
# backend/routers/example.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models.database import get_db
from schemas.example import ExampleRequest, ExampleResponse

router = APIRouter()

@router.post("/example", response_model=ExampleResponse)
async def create_example(
    request: ExampleRequest,
    db: Session = Depends(get_db)
):
    """
    新增範例端點
    """
    # 業務邏輯
    result = {"message": "Success"}
    return result
```

**註冊路由到 main.py**

```python
# backend/main.py
from routers import example

app.include_router(example.router, prefix="/api/v1/example", tags=["Example"])
```

#### Step 3: 撰寫測試

```python
# backend/tests/test_example.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_example():
    response = client.post("/api/v1/example", json={"data": "test"})
    assert response.status_code == 200
    assert response.json()["message"] == "Success"
```

#### Step 4: 執行測試

```bash
cd backend
pytest tests/ -v --cov=.
```

#### Step 5: Commit 與 Push

```bash
git add .
git commit -m "feat(example): add example endpoint

- Add POST /api/v1/example endpoint
- Add unit tests
- Update API documentation"

git push origin feature/your-feature-name
```

#### Step 6: 建立 Pull Request

前往 GitHub 建立 PR，等待 Code Review。

---

### 2. 前端開發流程

#### 新增頁面範例

```jsx
// frontend/src/pages/ExamplePage.jsx
import { useState } from 'react';

export default function ExamplePage() {
  const [data, setData] = useState(null);

  const fetchData = async () => {
    const response = await fetch('http://localhost:8000/api/v1/example');
    const result = await response.json();
    setData(result);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">Example Page</h1>
      <button
        onClick={fetchData}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Fetch Data
      </button>
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}
```

#### 註冊路由

```jsx
// frontend/src/App.jsx
import ExamplePage from './pages/ExamplePage';

function App() {
  return (
    <Router>
      <Routes>
        {/* 其他路由 */}
        <Route path="/example" element={<ExamplePage />} />
      </Routes>
    </Router>
  );
}
```

---

### 3. 資料庫遷移流程

#### 使用 Alembic 管理 Schema 變更

```bash
cd backend

# 建立遷移檔案
alembic revision --autogenerate -m "Add new column to TrainingTask"

# 檢視遷移檔案
cat alembic/versions/xxxx_add_new_column.py

# 執行遷移
alembic upgrade head

# 回退遷移
alembic downgrade -1
```

---

## 編碼規範

### Python 後端規範

#### 1. 遵循 PEP 8

```bash
# 使用 Black 自動格式化
black backend/ --line-length 100

# 使用 Flake8 檢查
flake8 backend/ --max-line-length=100

# 使用 mypy 檢查型別
mypy backend/ --ignore-missing-imports
```

#### 2. Type Hints 必須使用

```python
# ✅ 正確
def calculate_map(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]]
) -> float:
    pass

# ❌ 錯誤
def calculate_map(predictions, ground_truth):
    pass
```

#### 3. Docstring 規範（Google Style）

```python
def train_model(config: dict) -> str:
    """
    訓練 YOLO 模型

    Args:
        config (dict): 訓練配置參數
            - epochs (int): 訓練輪數
            - batch_size (int): 批次大小
            - model_type (str): 模型類型 (yolov5/yolov8/yolov11)

    Returns:
        str: 訓練結果儲存路徑

    Raises:
        ValueError: 配置參數無效時拋出
        RuntimeError: 訓練過程發生錯誤時拋出

    Example:
        >>> config = {"epochs": 100, "batch_size": 16, "model_type": "yolov8"}
        >>> result_path = train_model(config)
        >>> print(result_path)
        'runs/train/exp/weights/best.pt'
    """
    pass
```

#### 4. 錯誤處理

```python
# ✅ 正確：具體的錯誤處理
try:
    model = YOLO(model_path)
except FileNotFoundError:
    logger.error(f"模型檔案不存在: {model_path}")
    raise
except Exception as e:
    logger.error(f"載入模型失敗: {e}")
    raise RuntimeError(f"Failed to load model: {e}")

# ❌ 錯誤：捕捉所有錯誤不處理
try:
    model = YOLO(model_path)
except:
    pass
```

---

### React 前端規範

#### 1. 元件命名

```jsx
// ✅ 正確：PascalCase
function TrainingForm() {}
export default TrainingForm;

// ❌ 錯誤：camelCase
function trainingForm() {}
```

#### 2. Hooks 使用規範

```jsx
// ✅ 正確：Hook 在頂層呼叫
function MyComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  return <div>{data}</div>;
}

// ❌ 錯誤：條件式使用 Hook
function MyComponent() {
  if (someCondition) {
    const [data, setData] = useState(null); // 錯誤！
  }
}
```

#### 3. Props 解構

```jsx
// ✅ 正確
function Button({ label, onClick, disabled = false }) {
  return <button onClick={onClick} disabled={disabled}>{label}</button>;
}

// ❌ 錯誤
function Button(props) {
  return <button onClick={props.onClick}>{props.label}</button>;
}
```

#### 4. CSS 命名（Tailwind）

```jsx
// ✅ 正確：清晰的 utility classes
<div className="container mx-auto px-4 py-8">
  <h1 className="text-2xl font-bold text-gray-800 mb-4">Title</h1>
</div>

// ❌ 錯誤：過長的 class 字串
<div className="container mx-auto px-4 py-8 bg-white shadow-lg rounded-lg border border-gray-200 hover:shadow-xl transition-all duration-300 ease-in-out">
```

---

### Git Commit 規範

遵循 **Conventional Commits** 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 類型

- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔變更
- `style`: 格式變更（不影響代碼運行）
- `refactor`: 重構（不是新增功能或修復錯誤）
- `perf`: 效能優化
- `test`: 測試相關
- `chore`: 建置工具或輔助工具變動

#### 範例

```bash
# 新功能
git commit -m "feat(training): add resume training from checkpoint"

# 錯誤修復
git commit -m "fix(streaming): resolve camera connection timeout issue"

# 文檔更新
git commit -m "docs(readme): update installation instructions"

# 重構
git commit -m "refactor(dataset): extract validation logic to service layer"
```

---

## 測試指南

### 後端測試

#### 單元測試

```python
# backend/tests/test_training_service.py
import pytest
from services.training_service import TrainingService
from models.database import TestSessionLocal

@pytest.fixture
def db_session():
    """測試用資料庫 Session"""
    db = TestSessionLocal()
    yield db
    db.close()

def test_create_training_task(db_session):
    """測試建立訓練任務"""
    service = TrainingService(db_session)

    config = {
        "task_name": "test_task",
        "model_type": "yolov8",
        "epochs": 10
    }

    task = service.create_task(config)

    assert task.task_name == "test_task"
    assert task.status == "pending"
```

#### API 測試

```python
# backend/tests/test_api_training.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_start_training():
    """測試啟動訓練 API"""
    payload = {
        "task_name": "api_test",
        "model_type": "yolov8",
        "model_size": "n",
        "epochs": 10,
        "batch_size": 16
    }

    response = client.post("/api/v1/training/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
```

#### 執行測試

```bash
# 執行所有測試
pytest backend/tests/ -v

# 執行特定測試檔案
pytest backend/tests/test_training_service.py -v

# 執行特定測試函數
pytest backend/tests/test_training_service.py::test_create_training_task -v

# 生成覆蓋率報告
pytest backend/tests/ --cov=backend --cov-report=html

# 查看覆蓋率報告
open htmlcov/index.html
```

---

### 前端測試

#### 元件測試（使用 Vitest + React Testing Library）

```jsx
// frontend/src/components/__tests__/TrainingForm.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import TrainingForm from '../TrainingForm';

describe('TrainingForm', () => {
  it('renders form fields', () => {
    render(<TrainingForm onSubmit={() => {}} />);

    expect(screen.getByLabelText('Task Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Model Type')).toBeInTheDocument();
  });

  it('submits form with valid data', async () => {
    const mockSubmit = vi.fn();
    render(<TrainingForm onSubmit={mockSubmit} />);

    fireEvent.change(screen.getByLabelText('Task Name'), {
      target: { value: 'test_task' }
    });

    fireEvent.click(screen.getByText('Start Training'));

    expect(mockSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ task_name: 'test_task' })
    );
  });
});
```

#### 執行前端測試

```bash
cd frontend

# 執行測試
npm run test

# 執行測試並產生覆蓋率
npm run test:coverage

# 監聽模式（開發時使用）
npm run test:watch
```

---

## 除錯技巧

### 後端除錯

#### 1. 使用 Python Debugger (pdb)

```python
import pdb

def train_model(config):
    pdb.set_trace()  # 設定中斷點
    model = YOLO(config['model_type'])
    # ...
```

#### 2. 使用 FastAPI 自動文檔

訪問 http://localhost:8000/docs 測試 API 端點。

#### 3. 日誌記錄

```python
import logging

logger = logging.getLogger(__name__)

def process_dataset(path):
    logger.info(f"Processing dataset at {path}")
    try:
        # 處理邏輯
        logger.debug("Dataset processing details...")
    except Exception as e:
        logger.error(f"Failed to process dataset: {e}", exc_info=True)
```

#### 4. Redis 除錯

```bash
# 進入 Redis CLI
redis-cli

# 查看所有 keys
> KEYS *

# 查看隊列任務
> LRANGE rq:queue:training 0 -1

# 查看失敗任務
> LRANGE rq:queue:failed 0 -1

# 清空隊列
> DEL rq:queue:training
```

---

### 前端除錯

#### 1. React DevTools

安裝 [React Developer Tools](https://react.dev/learn/react-developer-tools) 瀏覽器擴充套件。

#### 2. Console Debugging

```jsx
function TrainingMonitor({ taskId }) {
  console.log('Rendering with taskId:', taskId);

  useEffect(() => {
    console.log('Effect triggered');
    fetchTrainingStatus(taskId);
  }, [taskId]);

  return <div>...</div>;
}
```

#### 3. Network 除錯

開啟瀏覽器開發者工具 → Network 標籤，檢查 API 請求與回應。

---

## 常見問題

### Q1: Redis 連線失敗

**錯誤訊息**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**解決方案**:
```bash
# 檢查 Redis 是否運行
redis-cli ping

# 啟動 Redis
# macOS
brew services start redis

# Ubuntu
sudo systemctl start redis
```

---

### Q2: RQ Worker 無法啟動

**錯誤訊息**: `ModuleNotFoundError: No module named 'ultralytics'`

**解決方案**:
```bash
# 確認虛擬環境已啟動
source backend/venv/bin/activate

# 重新安裝依賴
pip install -r backend/requirements.txt
```

---

### Q3: 前端 API 請求 CORS 錯誤

**錯誤訊息**: `Access to fetch at 'http://localhost:8000' has been blocked by CORS policy`

**解決方案**:
檢查 `backend/main.py` 的 CORS 配置是否包含前端 URL：
```python
allow_origins=[
    "http://localhost:5173",  # 確認此行存在
]
```

---

### Q4: 訓練任務卡在 pending 狀態

**原因**: RQ Worker 未運行或已崩潰

**解決方案**:
```bash
# 檢查 Worker 日誌
cd backend
source venv/bin/activate
rq worker training --verbose

# 查看 Redis 隊列
redis-cli
> LRANGE rq:queue:training 0 -1
```

---

## 貢獻指南

### 提交 Pull Request 前的檢查清單

- [ ] 程式碼遵循專案編碼規範
- [ ] 所有測試通過 (`pytest` + `npm run test`)
- [ ] 新增功能包含對應測試
- [ ] 更新相關文檔 (README.md, ARCHITECTURE.md 等)
- [ ] Commit 訊息遵循 Conventional Commits 格式
- [ ] 沒有 merge conflicts

### Code Review 標準

- **可讀性**: 變數命名清晰、邏輯易懂
- **效能**: 沒有明顯效能問題（N+1 查詢、不必要的迴圈）
- **安全性**: 輸入驗證、防止 SQL 注入
- **測試**: 測試覆蓋率足夠、測試案例合理

---

## 開發工具推薦

### IDE / 編輯器

- **VS Code** (推薦)
  - 擴充套件: Python, Pylance, ESLint, Prettier, Tailwind CSS IntelliSense
- **PyCharm Professional**
- **WebStorm**

### API 測試工具

- **Postman**
- **Insomnia**
- **HTTPie** (CLI)

### 資料庫管理

- **DBeaver** (支援 SQLite)
- **DB Browser for SQLite**

### Redis 管理

- **RedisInsight**
- **redis-cli** (內建 CLI 工具)

---

## 學習資源

### 官方文檔

- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [React 官方文檔](https://react.dev/)
- [Ultralytics YOLO 文檔](https://docs.ultralytics.com/)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)

### 推薦教學

- [Real Python - FastAPI Tutorial](https://realpython.com/fastapi-python-web-apis/)
- [React 官方教學 - Tic-Tac-Toe](https://react.dev/learn/tutorial-tic-tac-toe)
- [YOLO Object Detection Tutorial](https://docs.ultralytics.com/modes/train/)

---

**最後更新**: 2026-01-12
**版本**: 1.0.0

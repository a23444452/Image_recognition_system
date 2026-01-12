# Docker 容器路徑說明

## 📁 路徑對應關係

### Docker Volume 掛載

在 `docker-compose.yml` 中，我們配置了以下 volume 掛載：

```yaml
volumes:
  - ./datasets:/app/datasets
  - ./config:/app/config
  - ./models:/app/trained_models
```

這意味著：

| 宿主機路徑 | 容器內路徑 | 說明 |
|-----------|-----------|------|
| `./datasets/` | `/app/datasets/` | 資料集目錄 |
| `./config/` | `/app/config/` | 配置檔案目錄 |
| `./models/` | `/app/trained_models/` | 訓練模型目錄 |

---

## 🔍 絕對路徑如何運作

### ✅ 為什麼使用容器內的絕對路徑？

當您創建資料集時，系統會返回**容器內的絕對路徑**：

```json
{
  "path": "/app/datasets/d780dcb2-c847-4308-b36c-deb48020c6a1",
  "train_path": "/app/datasets/d780dcb2-c847-4308-b36c-deb48020c6a1/images/train",
  "val_path": "/app/datasets/d780dcb2-c847-4308-b36c-deb48020c6a1/images/val",
  "yaml_path": "/app/config/path_verification_test_d780dcb2.yaml"
}
```

### ✅ 這些路徑在哪裡有效？

**容器內的所有程序都可以訪問這些路徑**：

1. **後端 API** (backend 容器)
2. **訓練 Worker** (worker 容器)
3. **YOLO 訓練程序** (在 worker 容器內執行)

### ✅ 實際測試驗證

我們測試了以下場景，全部通過：

```python
# ✅ 讀取 YAML 檔案
with open('/app/config/dataset.yaml', 'r') as f:
    config = yaml.safe_load(f)

# ✅ 掃描訓練圖片
images = glob.glob('/app/datasets/.../images/train/*.jpg')

# ✅ 讀取標註檔案
with open('/app/datasets/.../labels/train/img1.txt', 'r') as f:
    labels = f.read()

# ✅ YOLO 訓練使用這些路徑
model.train(data='/app/config/dataset.yaml')
```

---

## 📊 完整路徑映射範例

### 範例：創建資料集 "my_dataset"

#### 1️⃣ 宿主機視角

```
Image_recognition_system/
├── datasets/
│   ├── raw_data/                    # 原始資料
│   └── abc123-def-456/              # 處理後的資料集
│       ├── images/
│       │   ├── train/
│       │   └── val/
│       └── labels/
│           ├── train/
│           └── val/
└── config/
    └── my_dataset_abc123.yaml       # 生成的 YAML
```

#### 2️⃣ 容器內視角

```
/app/
├── datasets/
│   ├── raw_data/                    # 對應宿主機 ./datasets/raw_data/
│   └── abc123-def-456/              # 對應宿主機 ./datasets/abc123-def-456/
│       ├── images/
│       │   ├── train/               # 容器內路徑: /app/datasets/abc123-def-456/images/train
│       │   └── val/                 # 容器內路徑: /app/datasets/abc123-def-456/images/val
│       └── labels/
│           ├── train/
│           └── val/
└── config/
    └── my_dataset_abc123.yaml       # 容器內路徑: /app/config/my_dataset_abc123.yaml
```

#### 3️⃣ API 返回的路徑

```json
{
  "train_path": "/app/datasets/abc123-def-456/images/train",
  "val_path": "/app/datasets/abc123-def-456/images/val",
  "yaml_path": "/app/config/my_dataset_abc123.yaml"
}
```

這些路徑：
- ✅ 在容器內有效
- ✅ YOLO 訓練可以直接使用
- ✅ 前端可以拿來填充訓練表單

---

## 🎯 實際使用場景

### 場景 1：創建資料集

**宿主機操作**：
```bash
# 將資料複製到 datasets 目錄
cp -r /path/to/my_images ./datasets/raw_images
```

**API 請求**：
```bash
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -d '{"name":"my_ds","source_folder":"./datasets/raw_images"}'
```

**API 回應**（容器內路徑）：
```json
{
  "train_path": "/app/datasets/uuid-xxx/images/train",
  "yaml_path": "/app/config/my_ds_uuid.yaml"
}
```

### 場景 2：開始訓練

**前端使用 API 返回的路徑**：
```javascript
const response = await fetch('/api/v1/datasets/');
const dataset = await response.json();

// 直接使用容器內路徑
const trainingConfig = {
  data: dataset.yaml_path,  // /app/config/my_ds_uuid.yaml
  epochs: 100
};

await fetch('/api/v1/training/start', {
  method: 'POST',
  body: JSON.stringify(trainingConfig)
});
```

**YOLO 訓練（在容器內執行）**：
```python
# worker 容器內執行
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
model.train(
    data='/app/config/my_ds_uuid.yaml',  # ✅ 容器內路徑直接可用
    epochs=100
)
```

---

## ⚠️ 重要注意事項

### ❌ 不要使用宿主機的絕對路徑

以下路徑在容器內**無法**訪問：

```json
{
  "train_path": "/Users/vincewang/Desktop/Project/datasets/...",  # ❌ 錯誤
  "train_path": "/home/user/datasets/...",                        # ❌ 錯誤
  "train_path": "C:\\Users\\...",                                 # ❌ 錯誤
}
```

### ✅ 始終使用容器內路徑

```json
{
  "train_path": "/app/datasets/...",    # ✅ 正確
  "yaml_path": "/app/config/...",       # ✅ 正確
}
```

---

## 🧪 測試路徑可訪問性

### 方法 1：使用 Docker Exec

```bash
# 測試路徑是否存在
docker-compose exec backend ls -la /app/datasets/

# 測試讀取 YAML
docker-compose exec backend cat /app/config/my_dataset.yaml

# 測試 Python 訪問
docker-compose exec backend python3 -c "
import os
print('Dataset exists:', os.path.exists('/app/datasets/uuid-xxx'))
"
```

### 方法 2：查看容器日誌

```bash
# 查看後端日誌
docker-compose logs backend --tail=50

# 查看 worker 日誌
docker-compose logs worker --tail=50
```

---

## 📝 常見問題

### Q1: 為什麼不直接使用宿主機路徑？

**答**：容器是隔離的環境，宿主機的檔案系統對容器不可見。只有通過 volume 掛載的目錄才能被容器訪問。

### Q2: 我可以訪問 datasets 目錄外的檔案嗎？

**答**：不行。只有在 docker-compose.yml 中掛載的目錄才能被訪問：
- ✅ `./datasets/` → `/app/datasets/`
- ✅ `./config/` → `/app/config/`
- ✅ `./models/` → `/app/trained_models/`
- ❌ 其他目錄無法訪問

### Q3: 如果我想訪問其他目錄怎麼辦？

**答**：修改 `docker-compose.yml` 添加新的 volume：

```yaml
volumes:
  - ./datasets:/app/datasets
  - ./config:/app/config
  - ./my_other_folder:/app/my_other_folder  # 新增掛載
```

然後重啟服務：
```bash
docker-compose down
docker-compose up -d
```

### Q4: 容器重啟後路徑還有效嗎？

**答**：是的！因為使用了 volume 掛載，資料持久化在宿主機。容器重啟後路徑依然有效。

---

## 🎓 總結

### 核心概念

1. **Volume 掛載** = 讓容器訪問宿主機檔案
2. **容器內路徑** = 統一的絕對路徑，適用於所有容器內程序
3. **路徑持久化** = 資料存在宿主機，容器重啟不影響

### 最佳實踐

- ✅ 所有資料放在 `./datasets/` 下
- ✅ 配置檔放在 `./config/` 下
- ✅ 訓練模型放在 `./models/` 下
- ✅ 使用 API 返回的容器內路徑
- ✅ 前端直接使用這些路徑填充表單

### 驗證方法

```bash
# 快速驗證：創建資料集後測試路徑
docker-compose exec backend python3 -c "
import yaml
with open('/app/config/your_dataset.yaml') as f:
    print(yaml.safe_load(f))
"
```

---

**最後更新**: 2026-01-12
**版本**: 1.0.0

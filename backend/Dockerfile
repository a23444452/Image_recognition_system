FROM python:3.10-slim

WORKDIR /app

# 設定非互動模式避免安裝過程中的提示
ENV DEBIAN_FRONTEND=noninteractive

# 安裝系統依賴（OpenCV 與編譯工具）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 複製 requirements
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 使用輕量級 Python 3.11
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統必要的編譯工具
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有代碼
COPY . .

# Zeabur 預設會給予 PORT 環境變數
ENV PORT 80
EXPOSE 80

# 啟動指令 (確保 main.py 存在)
CMD ["python", "main.py"]

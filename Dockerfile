FROM python:3.11-slim

# 安裝系統相依套件
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 yt-dlp（用 curl 下載最新版本）
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# 設定工作目錄
WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 啟動 Streamlit 應用
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false"]


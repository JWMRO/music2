FROM python:3.11-slim

# 安裝必要系統套件
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 yt-dlp（直接從官方）
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# 建立工作目錄
WORKDIR /app

# 複製專案檔案
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 預設執行 Streamlit 應用
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false"]

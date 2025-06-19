# Playwright専用サービス Dockerfile
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージを更新・インストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Node.js をインストール（Playwrightに必要）
RUN wget -qO- https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightブラウザをインストール
RUN playwright install chromium firefox webkit
RUN playwright install-deps

# アプリケーションコードをコピー
COPY app.py .

# 非rootユーザーを作成
RUN useradd -m -u 1000 playwright
RUN chown -R playwright:playwright /app
USER playwright

# ポートを公開
EXPOSE 8004

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/health')"

# アプリケーションを起動
CMD ["python", "app.py"]

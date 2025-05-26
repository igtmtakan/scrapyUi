# Multi-stage Docker build for ScrapyUI
FROM node:18-alpine AS nodejs-builder

# Install dependencies for Puppeteer
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Set Puppeteer to use installed Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Create app directory
WORKDIR /app/nodejs-service

# Copy package files
COPY nodejs-service/package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy Node.js source code
COPY nodejs-service/ ./

# Python stage
FROM python:3.11-slim AS python-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source code
COPY . ./

# Final stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    chromium \
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
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create non-root user
RUN groupadd -r scrapyui && useradd -r -g scrapyui -s /bin/bash scrapyui

# Create app directory
WORKDIR /app

# Copy Python application from builder
COPY --from=python-builder /app ./
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy Node.js application from builder
COPY --from=nodejs-builder /app/nodejs-service ./nodejs-service

# Install Node.js dependencies in final stage
WORKDIR /app/nodejs-service
RUN npm ci --only=production

# Set Puppeteer environment
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/uploads /app/exports \
    && chown -R scrapyui:scrapyui /app

# Switch to non-root user
USER scrapyui

# Set working directory back to app root
WORKDIR /app

# Expose ports
EXPOSE 8000 3001 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

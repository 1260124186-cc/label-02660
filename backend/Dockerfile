# ===== Backend Dockerfile =====
# 跨平台支持 ARM64 + AMD64
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖（poppler用于PDF转图片，libgl用于OpenCV）
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# 运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 从builder复制Python包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p logs output upload templates

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

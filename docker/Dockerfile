# PythonProject1 生产环境 — 基于 Python 3.11-slim
# 启动：docker run -p 8090:8090 pythonproject1:latest

FROM python:3.11-slim

WORKDIR /app

# 不缓冲输出、不写 .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 系统依赖：FFmpeg（成片必需）+ OpenCV 运行时库（部分领域 API）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件，利用 Docker 缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制完整项目
COPY . .

# 构建期自检（ffmpeg + 依赖 + Studio 库目录 + static/index.html）
# 自检失败则 docker build 失败，避免带病上线
RUN python main.py doctor

# runtime 目录（成片输出、日志、SQLite 库）
RUN mkdir -p runtime/outputs runtime/logs

# 对外暴露 Dashboard 端口
EXPOSE 8090

# 默认：启动 Web 控制台（监听所有接口）
# 可覆盖为 api：docker run ... python main.py api --host 0.0.0.0 --port 8000
CMD ["python", "main.py", "dashboard", "--host", "0.0.0.0", "--port", "8090"]

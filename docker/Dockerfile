# PythonProject1 生产环境
# 基于 Python 3.11-slim

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # FFmpeg
    ffmpeg \
    # 基础工具
    git \
    curl \
    # 清理
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY poc/requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt \
    # 安装可选依赖
    && pip install --no-cache-dir \
        kaleido \
        manim \
        imageio-ffmpeg

# 复制项目文件
COPY . .

# 创建输出目录
RUN mkdir -p /app/workspace/output

# 设置入口点
ENTRYPOINT ["python"]

# 默认命令
CMD ["poc/main.py"]

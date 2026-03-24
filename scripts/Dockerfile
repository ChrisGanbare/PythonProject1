# 数据可视化视频工作区：默认启动 Web 控制台（与 README 一致）
# 构建: docker build -t video-project .
# 运行: docker run --rm -p 8090:8090 -v "%CD%/runtime:/app/runtime" video-project   (Windows)
#       docker run --rm -p 8090:8090 -v "$(pwd)/runtime:/app/runtime" video-project   (Unix)

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/projects

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY . .

RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/runtime/outputs /app/runtime/logs /app/runtime/cache /app/runtime/temp

EXPOSE 8090

CMD ["python", "-m", "uvicorn", "dashboard:app", "--host", "0.0.0.0", "--port", "8090"]

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Runtime libraries needed by matplotlib/opencv/ffmpeg flows.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/runtime/outputs /app/runtime/logs /app/runtime/cache /app/runtime/temp

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "PythonProject1.main:app", "--host", "0.0.0.0", "--port", "8000"]

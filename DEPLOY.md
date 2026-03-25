# PythonProject1 部署文档

## 快速部署

### 方法 1: 本地部署 (推荐开发使用)

```bash
# 1. 克隆项目
git clone https://github.com/ChrisGanbare/PythonProject1.git
cd PythonProject1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python main.py dashboard  # Web 控制台 (8090)
# 或
python main.py api        # API 服务 (8000)

# 4. 运行 POC 演示 (可选)
cd poc
python demo_stages.py
```

### 方法 2: Docker 部署 (推荐生产使用)

```bash
# 1. 构建镜像
docker build -f docker/Dockerfile -t pythonproject1:latest .

# 2. 运行容器
docker run -it -v $(pwd)/workspace:/app/workspace pythonproject1:latest

# 3. 使用 docker-compose
cd docker
docker-compose up -d
```

### 方法 3: Docker Compose (多服务)

```bash
cd docker

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 📦 远程部署检查清单

### 部署前检查

- [ ] 已安装 Python 3.9+
- [ ] 已克隆项目
- [ ] 已安装依赖 (`pip install -r requirements.txt`)
- [ ] 已配置防火墙 (端口 8000 和 8090)

### 启动服务

**API 服务**:
```bash
python main.py api --host 0.0.0.0 --port 8000
```

**Dashboard 控制台**:
```bash
python main.py dashboard --host 0.0.0.0 --port 8090
```

### 远程访问

- **API 文档**: `http://<服务器 IP>:8000/docs`
- **Dashboard**: `http://<服务器 IP>:8090`

### 验证步骤

1. [ ] 访问 API 文档页面
2. [ ] 访问 Dashboard 页面
3. [ ] 测试创建视频作业
4. [ ] 检查日志无错误

---

## 环境要求

### 系统要求

| 系统 | 版本 | 必需 |
|------|------|------|
| Python | 3.9+ | ✅ |
| FFmpeg | 5.0+ | ✅ (视频处理) |
| Docker | 20.0+ | ⏸️ (可选) |
| Git | 2.0+ | ✅ |

### Python 依赖

核心依赖:
```
plotly>=5.18.0
numpy>=1.24.0
pandas>=2.0.0
Pillow>=10.0.0
pytest>=7.4.0
```

可选依赖:
```
kaleido          # 静态图片导出
moviepy>=2.0.0   # 视频处理
manim>=0.18.0    # 动画引擎
imageio-ffmpeg   # 视频编码
```

---

## 部署步骤详解

### 步骤 1: 环境检查

```bash
python deploy.py check
```

输出示例:
```
============================================================
PythonProject1 完整部署
============================================================

环境检查:

Python 版本:
✓ Python 3.11.0

FFmpeg:
✓ FFmpeg: 5.1.2

Docker:
✓ Docker: 24.0.0

Python 依赖:
✓ plotly
✓ numpy
✓ pandas
✓ PIL
✓ pytest
```

### 步骤 2: 安装依赖

```bash
# 基础依赖
python deploy.py install

# 完整依赖 (包括可选)
pip install -r poc/requirements.txt
pip install kaleido moviepy manim imageio-ffmpeg
```

### 步骤 3: 创建工作目录

自动创建以下目录:
```
workspace/
├── output/    # 输出文件
├── temp/      # 临时文件
├── cache/     # 缓存
└── config.ini # 配置文件
```

### 步骤 4: 运行测试

```bash
python deploy.py test
```

### 步骤 5: 运行演示

```bash
python deploy.py demo
```

### 步骤 6: Docker 构建 (可选)

```bash
python deploy.py docker
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FFMPEG_CONFIG` | medium | 编码质量 (low/medium/high) |
| `MAX_WORKERS` | 4 | 最大工作线程数 |
| `PYTHONUNBUFFERED` | 1 | 无缓冲输出 |

### 配置文件 (config.ini)

```ini
[video]
width = 1920
height = 1080
fps = 30
bitrate = 5000k
codec = libx264

[audio]
codec = aac
bitrate = 192k
sample_rate = 44100

[performance]
max_workers = 4
cache_enabled = true
hardware_accel = false

[output]
format = mp4
quality = high
```

---

## 生产环境部署

### AWS EC2

```bash
# 1. 启动 EC2 实例 (Ubuntu 22.04)

# 2. 安装依赖
sudo apt update
sudo apt install -y python3-pip ffmpeg docker.io

# 3. 克隆项目
git clone <repo-url>
cd PythonProject1

# 4. 部署
cd poc
python3 deploy.py deploy

# 5. 使用 Docker
cd ../docker
sudo docker-compose up -d
```

### Google Cloud Run

```bash
# 1. 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/pythonproject1

# 2. 部署到 Cloud Run
gcloud run deploy pythonproject1 \
  --image gcr.io/PROJECT_ID/pythonproject1 \
  --platform managed
```

### Azure Container Instances

```bash
# 1. 创建资源组
az group create --name myResourceGroup --location eastus

# 2. 部署容器
az container create \
  --resource-group myResourceGroup \
  --name pythonproject1 \
  --image pythonproject1:latest \
  --cpu 2 \
  --memory 4
```

---

## 故障排查

### FFmpeg 未找到

**Windows:**
```powershell
choco install ffmpeg
# 或下载 https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg  # RHEL/CentOS
```

### Docker 权限问题

```bash
# Linux: 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 或使用 sudo
sudo docker run ...
```

### Python 依赖冲突

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

---

## 性能优化

### 硬件加速

```ini
# config.ini
[performance]
hardware_accel = true
gpu_encoder = h264_nvenc  # NVIDIA
# gpu_encoder = h264_amf  # AMD
# gpu_encoder = h264_videotoolbox  # macOS
```

### 并行处理

```ini
[performance]
max_workers = 8  # 根据 CPU 核心数调整
```

### 缓存启用

```ini
[performance]
cache_enabled = true
```

---

## 监控与日志

### 查看 Docker 日志

```bash
docker-compose logs -f app
```

### 健康检查

```bash
# 检查服务状态
docker-compose ps

# 检查容器健康
docker inspect --format='{{.State.Health.Status}}' <container-id>
```

---

## 更新与升级

### 更新代码

```bash
git pull origin main
python deploy.py deploy
```

### 升级依赖

```bash
python deploy.py install --upgrade
```

### 重建 Docker 镜像

```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 安全建议

1. **不要提交敏感信息**
   - 使用环境变量存储密钥
   - 添加 `.env` 到 `.gitignore`

2. **限制容器权限**
   ```yaml
   # docker-compose.yml
   services:
     app:
       security_opt:
         - no-new-privileges:true
       read_only: true
   ```

3. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```

---

## 支持

- 文档：`/docs`
- 问题：GitHub Issues
- 邮件：support@example.com

---

*最后更新：2026-03-24*  
*版本：1.0.0*

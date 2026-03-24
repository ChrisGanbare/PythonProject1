# PythonProject1 - 远程部署指南

**版本**: v2.2  
**最后更新**: 2026-03-24

---

## 🚀 快速部署

### 1. 克隆项目

```bash
# 克隆项目
git clone https://github.com/ChrisGanbare/PythonProject1.git
cd PythonProject1
```

### 2. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt
```

### 3. 启动程序

#### 方式 1: 使用 start.py (推荐)

```bash
# 启动 API 服务
python start.py api

# 启动 Dashboard
python start.py dashboard

# 运行演示
python start.py demo

# 查看帮助
python start.py --help
```

#### 方式 2: 直接启动

```bash
# API 服务
python -m api.main --port 8000

# Dashboard
python scripts/dashboard.py

# CLI 工具
python -m cli.video list-templates
```

---

## 🌐 远程访问配置

### API 服务 (默认端口 8000)

**启动命令**:
```bash
python start.py api --host 0.0.0.0 --port 8000
```

**访问地址**:
- Swagger UI: `http://<服务器 IP>:8000/docs`
- API 根路径：`http://<服务器 IP>:8000`

**防火墙设置**:
```bash
# Windows (管理员权限)
netsh advfirewall firewall add rule name="PythonProject1 API" dir=in action=allow protocol=TCP localport=8000

# Linux
sudo ufw allow 8000/tcp

# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
```

---

### Dashboard 控制台 (默认端口 8090)

**启动命令**:
```bash
python start.py dashboard --host 0.0.0.0 --port 8090
```

**访问地址**:
- Dashboard: `http://<服务器 IP>:8090`

**防火墙设置**:
```bash
# Windows
netsh advfirewall firewall add rule name="PythonProject1 Dashboard" dir=in action=allow protocol=TCP localport=8090

# Linux
sudo ufw allow 8090/tcp
```

---

## 📦 系统要求

### 最低要求

- **Python**: 3.9+
- **内存**: 4GB
- **磁盘**: 2GB
- **操作系统**: Windows/Linux/macOS

### 推荐配置

- **Python**: 3.11+
- **内存**: 8GB+
- **磁盘**: 10GB+
- **操作系统**: Windows 10+/Ubuntu 20.04+/macOS 11+

---

## 🔧 依赖安装

### Windows

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 FFmpeg (可选，用于视频渲染)
choco install ffmpeg
# 或下载 https://ffmpeg.org/download.html
```

### Linux (Ubuntu/Debian)

```bash
# 系统依赖
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg

# Python 依赖
pip3 install -r requirements.txt
```

### macOS

```bash
# 系统依赖
brew install python ffmpeg

# Python 依赖
pip3 install -r requirements.txt
```

---

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -f scripts/Dockerfile -t pythonproject1:latest .
```

### 运行容器

```bash
# API 服务
docker run -d -p 8000:8000 --name pp1-api pythonproject1:latest python start.py api

# Dashboard
docker run -d -p 8090:8090 --name pp1-dashboard pythonproject1:latest python start.py dashboard
```

### 使用 Docker Compose

```bash
cd scripts
docker-compose up -d
```

---

## 🔐 安全配置

### 生产环境建议

1. **限制访问 IP**:
   ```bash
   # 只允许特定 IP 访问
   python start.py api --host 127.0.0.1
   ```

2. **使用反向代理**:
   ```nginx
   # Nginx 配置示例
   location /api/ {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

3. **启用 HTTPS**:
   ```bash
   # 使用 Let's Encrypt
   certbot --nginx -d your-domain.com
   ```

4. **设置环境变量**:
   ```bash
   # .env 文件
   API_KEY=your-secret-key
   DATABASE_URL=postgresql://user:pass@localhost/dbname
   ```

---

## 📊 验证部署

### 检查 API 服务

```bash
# 访问 API 文档
curl http://<服务器 IP>:8000/docs

# 列出模板
curl http://<服务器 IP>:8000/api/v1/templates

# 列出主题
curl http://<服务器 IP>:8000/api/v1/themes
```

### 检查 Dashboard

```bash
# 访问 Dashboard
curl http://<服务器 IP>:8090

# 检查项目列表
curl http://<服务器 IP>:8090/api/registry
```

---

## 🐛 故障排查

### 常见问题

#### 1. 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

#### 2. 模块导入错误

**错误**: `ModuleNotFoundError`

**解决**:
```bash
# 确保在项目根目录运行
cd PythonProject1
python start.py api
```

#### 3. FFmpeg 未找到

**错误**: `FFmpeg not found`

**解决**:
```bash
# Windows
choco install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

## 📝 更新项目

```bash
# 拉取最新代码
git pull origin master

# 重新安装依赖
pip install -r requirements.txt --upgrade

# 重启服务
# (先停止当前运行的服务，然后重新启动)
```

---

## 📞 支持

- **项目地址**: https://github.com/ChrisGanbare/PythonProject1
- **Issue 反馈**: https://github.com/ChrisGanbare/PythonProject1/issues
- **文档**: http://<服务器 IP>:8000/docs

---

**部署完成，祝使用愉快！** 🎉

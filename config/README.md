# 配置目录

包含项目配置文件：

- `.env` - 环境变量
- `.env.example` - 环境变量模板
- `Dockerfile` - Docker 镜像配置
- `pyproject.toml` - Python 项目配置
- `requirements-console.txt` - 控制台依赖

使用方式:

```bash
# 复制环境变量模板
cp scripts/.env.example .env

# 构建 Docker 镜像
docker build -f scripts/Dockerfile -t pythonproject1:latest .
```

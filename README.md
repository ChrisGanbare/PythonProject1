# PythonProject1 - Free Ride 自动化演示

## 📋 功能特性
- ✅ **现代化 Python 项目结构**：遵循 PEP 标准
- ✅ **FastAPI Web 框架**：高性能异步 Web 框架
- ✅ **自动化测试**：pytest + coverage
- ✅ **代码质量**：Black、Flake8、Mypy
- ✅ **CI/CD**：GitHub Actions 自动化流水线
- ✅ **容器化**：Docker 支持
- ✅ **API 文档**：自动生成 Swagger UI

## 🚀 快速开始
```bash
# 克隆项目
git clone <your-repo>
cd PythonProject1

# 安装依赖
pip install -e .[dev]

# 开发模式
./scripts/dev.sh

# 运行测试
./scripts/test.sh

# 构建 Docker 镜像
docker build -t pythonproject1 .
```

## 📊 API 端点
- `GET /health` - 服务健康状态
- `GET /` - 应用主页
- `GET /docs` - 自动生成的 API 文档 (Swagger UI)
- `GET /redoc` - 替代 API 文档 (ReDoc)

## 🧪 测试覆盖
- 单元测试覆盖率目标：≥90%
- 代码格式化：Black 自动格式化
- 类型检查：Mypy 静态类型检查
- 代码规范：Flake8 PEP8 检查
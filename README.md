# PythonProject1 - Free Ride 自动化演示

## 📋 功能特性
- ✅ **现代化 Python 项目结构**：遵循 PEP 标准
- ✅ **贷款还款对比动画**：等额本息 vs 等额本金可视化
- ✅ **电影级数据可视化**：Flourish 风格，抖音/B站竖屏适配
- ✅ **自动化测试**：pytest + coverage
- ✅ **代码质量**：Black、Flake8、Mypy
- ✅ **CI/CD**：GitHub Actions 自动化流水线
- ✅ **容器化**：Docker 支持

## 🎬 贷款动画脚本
`loan_animation_pro.py` - 专业的贷款还款方式对比动画生成器

**特点**：
- 30秒竖屏视频（1080×1920）
- 等额本息 vs 等额本金对比
- 实时计算和动态可视化
- 电影级视觉效果

**运行要求**：
- Python 3.8+
- FFmpeg（视频编码）
- Matplotlib, NumPy

## 🚀 快速开始
```bash
# 克隆项目
git clone https://github.com/ChrisGanbare/PythonProject1.git
cd PythonProject1

# 安装依赖
pip install -e .[dev]

# 运行贷款动画脚本
python loan_animation_pro.py

# 开发模式（如果需要Web API）
uvicorn src.PythonProject1.main:app --reload
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
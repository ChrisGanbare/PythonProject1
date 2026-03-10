from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="PythonProject1",
    description="Free Ride 自动化演示项目",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "PythonProject1"
    }

@app.get("/")
async def root():
    """主页面端点"""
    return {
        "message": "Free Ride Python 自动化演示成功！",
        "features": [
            "自动化测试",
            "代码格式化",
            "类型检查",
            "API 文档",
            "Docker 容器化"
        ],
        "version": "1.0.0"
    }
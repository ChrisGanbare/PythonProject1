import pytest
from fastapi.testclient import TestClient
from src.PythonProject1.main import app

client = TestClient(app)

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"

def test_root_endpoint():
    """测试主页面端点"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Free Ride Python 自动化演示成功！" in response.json()["message"]
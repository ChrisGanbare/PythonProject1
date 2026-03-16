"""
FastAPI 端点测试
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from src.PythonProject1.main import app


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


class TestHealthCheck:
    """健康检查端点测试"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestRoot:
    """主页面端点测试"""
    
    def test_root(self, client):
        """测试根路由"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data


class TestLoanSummary:
    """贷款摘要端点测试"""
    
    def test_loan_summary_default(self, client):
        """测试默认参数的贷款摘要"""
        response = client.post("/api/loan/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["loan_amount"] == 1_000_000
        assert data["annual_rate"] == 0.045
        assert data["loan_years"] == 30
        assert "equal_interest" in data
        assert "equal_principal" in data
        assert "comparison" in data
    
    def test_loan_summary_custom(self, client):
        """测试自定义参数的贷款摘要"""
        response = client.post(
            "/api/loan/summary",
            params={
                "loan_amount": 2_000_000,
                "annual_rate": 0.05,
                "loan_years": 20,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["loan_amount"] == 2_000_000
        assert data["annual_rate"] == 0.05
        assert data["loan_years"] == 20
    
    def test_loan_summary_invalid_amount(self, client):
        """测试无效贷款金额"""
        response = client.post(
            "/api/loan/summary",
            params={
                "loan_amount": 1000,  # 太低
            }
        )
        
        assert response.status_code == 400
    
    def test_loan_summary_invalid_rate(self, client):
        """测试无效利率"""
        response = client.post(
            "/api/loan/summary",
            params={
                "annual_rate": 0.5,  # 太高
            }
        )
        
        assert response.status_code == 400


class TestVideoGeneration:
    """视频生成端点测试"""
    
    def test_generate_video_default(self, client):
        """测试默认参数的视频生成"""
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "task_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data
    
    def test_generate_video_custom(self, client):
        """测试自定义参数的视频生成"""
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 500_000,
                "annual_rate": 0.04,
                "loan_years": 25,
                "video_duration": 60,
                "fps": 60,
                "include_subtitles": True,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data


class TestTaskStatus:
    """任务状态端点测试"""
    
    def test_get_task_status(self, client):
        """测试获取任务状态"""
        # 先创建任务
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            }
        )
        
        task_id = response.json()["task_id"]
        
        # 获取任务状态
        response = client.get(f"/api/task/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == task_id
        assert data["status"] in ["queued", "processing", "completed", "failed"]
        assert "progress" in data
        assert "created_at" in data
    
    def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/task/nonexistent-task-id")
        
        assert response.status_code == 404


class TestTaskResult:
    """任务结果端点测试"""
    
    def test_get_task_result(self, client):
        """测试获取任务结果"""
        # 先创建任务
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            }
        )
        
        task_id = response.json()["task_id"]
        
        # 获取任务结果
        response = client.get(f"/api/task/{task_id}/result")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == task_id
        assert data["status"] in ["queued", "processing", "completed", "failed"]
    
    def test_get_nonexistent_task_result(self, client):
        """测试获取不存在的任务结果"""
        response = client.get("/api/task/nonexistent-task-id/result")
        
        assert response.status_code == 404


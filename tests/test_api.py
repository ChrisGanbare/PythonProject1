"""FastAPI endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from loan_comparison.api.main import app


@pytest.fixture(autouse=True)
def _stub_background(monkeypatch):
    def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("loan_comparison.api.main._generate_video_background", _noop)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthCheck:
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"


class TestRoot:
    def test_root(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data


class TestLoanSummary:
    def test_loan_summary_default(self, client: TestClient):
        response = client.post("/api/loan/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["loan_amount"] == 1_000_000
        assert data["annual_rate"] == 0.045
        assert data["loan_years"] == 30
        assert "equal_interest" in data
        assert "equal_principal" in data
        assert "comparison" in data

    def test_loan_summary_custom(self, client: TestClient):
        response = client.post(
            "/api/loan/summary",
            params={
                "loan_amount": 2_000_000,
                "annual_rate": 0.05,
                "loan_years": 20,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["loan_amount"] == 2_000_000
        assert data["annual_rate"] == 0.05
        assert data["loan_years"] == 20

    def test_loan_summary_invalid_amount(self, client: TestClient):
        response = client.post("/api/loan/summary", params={"loan_amount": 1000})
        assert response.status_code == 422

    def test_loan_summary_invalid_rate(self, client: TestClient):
        response = client.post("/api/loan/summary", params={"annual_rate": 0.5})
        assert response.status_code == 422


class TestVideoGeneration:
    def test_generate_video_default(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data


class TestTaskStatus:
    def test_get_task_status(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )
        task_id = response.json()["task_id"]

        response = client.get(f"/api/task/{task_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == task_id
        assert data["status"] in ["queued", "processing", "completed", "failed"]
        assert "progress" in data
        assert "created_at" in data

    def test_get_nonexistent_task(self, client: TestClient):
        response = client.get("/api/task/nonexistent-task-id")
        assert response.status_code == 404


class TestTaskResult:
    def test_get_task_result(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )
        task_id = response.json()["task_id"]

        response = client.get(f"/api/task/{task_id}/result")

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == task_id
        assert data["status"] in ["queued", "processing", "completed", "failed"]

    def test_get_nonexistent_task_result(self, client: TestClient):
        response = client.get("/api/task/nonexistent-task-id/result")
        assert response.status_code == 404

"""FastAPI endpoint tests for fund_fee_erosion."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fund_fee_erosion.api.main import app


@pytest.fixture(autouse=True)
def _stub_background(monkeypatch):
    monkeypatch.setattr(
        "fund_fee_erosion.api.main._generate_video_background",
        lambda *args, **kwargs: None,
    )


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


class TestFundSummary:
    def test_summary_default(self, client: TestClient):
        response = client.get("/api/fund/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["principal"] == 1_000_000
        assert data["gross_return"] == 0.08
        assert data["years"] == 30
        assert "scenarios" in data
        # 4 default fee scenarios
        assert len(data["scenarios"]) == 4

    def test_summary_custom(self, client: TestClient):
        response = client.get(
            "/api/fund/summary",
            params={"principal": 500_000, "gross_return": 0.06, "years": 20},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["principal"] == 500_000
        assert data["gross_return"] == 0.06
        assert data["years"] == 20

    def test_summary_scenarios_ordered(self, client: TestClient):
        response = client.get("/api/fund/summary")
        data = response.json()["scenarios"]
        # Zero fee should have highest final value
        zero_val  = data["zero"]["final_value"]
        etf_val   = data["etf"]["final_value"]
        active_val = data["active"]["final_value"]
        high_val  = data["high"]["final_value"]
        assert zero_val > etf_val > active_val > high_val

    def test_summary_invalid_principal(self, client: TestClient):
        response = client.get("/api/fund/summary", params={"principal": 1000})
        assert response.status_code == 422

    def test_summary_invalid_return(self, client: TestClient):
        response = client.get("/api/fund/summary", params={"gross_return": 1.5})
        assert response.status_code == 422

    def test_summary_invalid_years(self, client: TestClient):
        response = client.get("/api/fund/summary", params={"years": 0})
        assert response.status_code == 422


class TestVideoGeneration:
    def test_generate_video_default(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={"principal": 1_000_000, "gross_return": 0.08, "years": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data

    def test_generate_video_custom_params(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={"principal": 2_000_000, "gross_return": 0.10, "years": 20},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    def test_generate_video_invalid_principal(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={"principal": -1000},
        )
        assert response.status_code == 422


class TestTaskStatus:
    def test_get_task_status(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={"principal": 1_000_000, "gross_return": 0.08, "years": 30},
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
        response = client.get("/api/task/nonexistent-id")
        assert response.status_code == 404


class TestTaskResult:
    def test_get_task_result(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={"principal": 1_000_000, "gross_return": 0.08, "years": 30},
        )
        task_id = response.json()["task_id"]

        response = client.get(f"/api/task/{task_id}/result")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] in ["queued", "processing", "completed", "failed"]

    def test_get_nonexistent_task_result(self, client: TestClient):
        response = client.get("/api/task/nonexistent-id/result")
        assert response.status_code == 404

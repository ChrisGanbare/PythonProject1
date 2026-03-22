"""FastAPI endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from typing import Iterator

from ..api.main import app


@pytest.fixture(autouse=True)
def _stub_background(monkeypatch):
    def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr("loan_comparison.api.main._generate_video_background", _noop)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


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


class TestContentPreview:
    def test_preview_content_plan(self, client: TestClient):
        response = client.post(
            "/api/content/preview",
            json={
                "platform": "douyin",
                "style": "tech",
                "content_variant": "short",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "douyin"
        assert data["style"] == "tech"
        assert data["variant"] == "short"
        assert len(data["beats"]) == 4
        assert data["beats"][0]["beat_type"] == "hook"
        assert data["beats"][0]["narration"].startswith("先把结论砸出来")
        assert data["conclusion_card"]["title"]


class TestScreenplayPreview:
    def test_list_screenplay_providers(self, client: TestClient):
        response = client.get("/api/screenplay/providers")

        assert response.status_code == 200
        data = response.json()
        assert any(item["name"] == "mock" for item in data)
        assert any(item["is_default"] for item in data)

    def test_preview_screenplay(self, client: TestClient):
        response = client.post(
            "/api/screenplay/preview",
            json={
                "platform": "douyin",
                "style": "tech",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "topic": "房贷利息真相",
                "screenplay_provider": "mock",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider_used"] == "mock"
        assert data["fallback_used"] is False
        assert data["screenplay"]["topic"] == "房贷利息真相"
        assert len(data["screenplay"]["scenes"]) >= 4

    def test_preview_screenplay_rejects_unknown_provider(self, client: TestClient):
        response = client.post(
            "/api/screenplay/preview",
            json={
                "platform": "douyin",
                "style": "tech",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "screenplay_provider": "unknown_provider",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["provider_used"] == "mock"

    def test_edit_screenplay(self, client: TestClient):
        preview = client.post(
            "/api/screenplay/preview",
            json={
                "platform": "douyin",
                "style": "tech",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "topic": "贷款对比",
            },
        )
        screenplay = preview.json()["screenplay"]

        response = client.patch(
            "/api/screenplay/preview",
            json={
                "screenplay": screenplay,
                "title": "贷款对比｜二次改稿",
                "scene_narration_overrides": {
                    screenplay["scenes"][0]["id"]: "新的开场钩子文案"
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["screenplay"]["title"] == "贷款对比｜二次改稿"
        assert data["screenplay"]["scenes"][0]["narration"] == "新的开场钩子文案"
        assert screenplay["scenes"][0]["id"] in data["changed_scene_ids"]


class TestVideoGeneration:
    def test_generate_video_default(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "platform": "douyin",
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

    def test_generate_video_accepts_quality(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "platform": "douyin",
                "quality": "preview",
                "burn_subtitles": False,
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 200

    def test_generate_video_rejects_invalid_quality(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "platform": "douyin",
                "quality": "ultra",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 422

    def test_generate_video_requires_platform(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 422

    def test_generate_video_rejects_invalid_duration_for_platform(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "platform": "douyin",
                "video_duration": 10,
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
            },
        )

        assert response.status_code == 422


class TestTaskStatus:
    def test_get_task_status(self, client: TestClient):
        response = client.post(
            "/api/generate-video",
            json={
                "platform": "douyin",
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
                "platform": "douyin",
                "quality": "preview",
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
        assert data["platform"] == "douyin"
        assert data["quality"] == "preview"
        assert "content_style" in data
        assert "content_variant" in data
        assert "conclusion_card_title" in data
        assert "theme_name" in data
        assert "visual_focus" in data
        assert "subtitle_burned" in data
        assert "bgm_applied" in data
        assert "rendered_video_path" in data
        assert "final_video_path" in data
        assert "subtitle_path" in data
        assert "styled_subtitle_path" in data
        assert "subtitle_render_mode" in data
        assert "cover_path" in data

    def test_get_nonexistent_task_result(self, client: TestClient):
        response = client.get("/api/task/nonexistent-task-id/result")
        assert response.status_code == 404


class TestScriptLibrary:
    @pytest.fixture
    def lib_client(self, tmp_path, monkeypatch):
        from shared.library.screenplay_store import ScreenplayStore

        monkeypatch.setattr(
            "loan_comparison.api.main.screenplay_store",
            ScreenplayStore(db_path=tmp_path / "library_api.db"),
        )
        with TestClient(app) as test_client:
            yield test_client

    def test_list_assets(self, lib_client: TestClient):
        response = lib_client.get("/api/library/assets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(item["id"] == "music_upbeat_01" for item in data)

    def test_create_script_and_refine(self, lib_client: TestClient):
        preview = lib_client.post(
            "/api/screenplay/preview",
            json={
                "platform": "douyin",
                "style": "tech",
                "loan_amount": 1_000_000,
                "annual_rate": 0.045,
                "loan_years": 30,
                "topic": "贷款对比",
                "screenplay_provider": "mock",
            },
        )
        assert preview.status_code == 200
        sp = preview.json()["screenplay"]

        create = lib_client.post(
            "/api/library/scripts",
            json={
                "goal": "科普",
                "platform": "douyin",
                "topic": "贷款",
                "screenplay": sp,
            },
        )
        assert create.status_code == 200
        script_id = create.json()["script_id"]

        refine = lib_client.post(
            f"/api/library/scripts/{script_id}/refine",
            json={"edit_instruction": "缩短开场旁白", "scene_narration_overrides": {}},
        )
        assert refine.status_code == 200
        assert refine.json()["version"] == 2

        versions = lib_client.get(f"/api/library/scripts/{script_id}/versions")
        assert versions.status_code == 200
        assert len(versions.json()) >= 2

        approve = lib_client.post(f"/api/library/scripts/{script_id}/versions/2/approve")
        assert approve.status_code == 200
        assert approve.json()["status"] == "approved"

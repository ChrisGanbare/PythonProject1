from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard import app, REPO_ROOT

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

def test_index_html(client):
    """Test standard index.html is served."""
    # Ensure static file exists or mock it? 
    # For e2e, we assume static/index.html is created by previous steps.
    # But if not, we create a dummy one for test isolation if needed.
    # We'll just check if it gets 200 or 404.
    response = client.get("/")
    if not (REPO_ROOT / "web" / "index.html").exists():
        pytest.skip("web/index.html not found, skipping UI test")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_registry_discovery(client):
    """Test project registry discovery API."""
    response = client.get("/api/registry")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "reference_project_names" in data
    assert "loan_comparison" in data["reference_project_names"]

    by_name = {p["name"]: p for p in data["projects"]}
    assert by_name["loan_comparison"]["deletable"] is False
    assert by_name["fund_fee_erosion"]["deletable"] is False

    # Check for known projects
    project_names = [p["name"] for p in data["projects"]]
    assert "loan_comparison" in project_names
    assert "fund_fee_erosion" in project_names
    assert "video_platform_introduction" in project_names


def test_delete_reference_project_forbidden(client):
    response = client.delete("/api/projects/loan_comparison")
    assert response.status_code == 403


def test_create_and_delete_project_roundtrip(client):
    name = f"e2e_del_{uuid.uuid4().hex[:10]}"
    create = client.post("/api/projects", json={"name": name, "description": "e2e temp"})
    assert create.status_code == 200
    reg = client.get("/api/registry").json()
    assert name in [p["name"] for p in reg["projects"]]
    assert next(p for p in reg["projects"] if p["name"] == name)["deletable"] is True

    delete = client.post("/api/projects/delete", json={"name": name})
    assert delete.status_code == 200
    reg2 = client.get("/api/registry").json()
    assert name not in [p["name"] for p in reg2["projects"]]


def test_delete_project_delete_method_still_works(client):
    name = f"e2e_del_del_{uuid.uuid4().hex[:8]}"
    assert client.post("/api/projects", json={"name": name, "description": "x"}).status_code == 200
    r = client.delete(f"/api/projects/{name}")
    assert r.status_code == 200
    assert name not in [p["name"] for p in client.get("/api/registry").json()["projects"]]


def test_registry_exposes_screenplay_capabilities(client):
    response = client.get("/api/registry")
    assert response.status_code == 200

    projects = {project["name"]: project for project in response.json()["projects"]}
    assert projects["loan_comparison"]["capabilities"]["screenplay_workflow"] is True
    assert projects["video_platform_introduction"]["capabilities"]["screenplay_workflow"] is True
    assert projects["fund_fee_erosion"].get("capabilities", {}).get("screenplay_workflow") in {None, False}

def test_inspect_loan_smoke_check(client):
    """Test inspecting a specific task parameter schema."""
    response = client.get("/api/inspect/loan_comparison/smoke_check")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "run_smoke_check"
    # smoke_check has no params, so parameters list might be empty
    assert isinstance(data["parameters"], list)

def test_inspect_loan_animation(client):
    """Test inspecting a task with parameters."""
    response = client.get("/api/inspect/loan_comparison/loan_animation")
    assert response.status_code == 200
    data = response.json()
    params = {p["name"]: p for p in data["parameters"]}
    
    assert "output_file" in params
    assert "platform" in params
    assert params["platform"]["type"] in [
        "str",
        "NoneType",
        "any",
        "Optional",
        "str | None",
        "Optional[str]",
    ]  # typing 因版本而异


def test_inspect_intro_video_task(client):
    response = client.get("/api/inspect/video_platform_introduction/generate_intro_video")
    assert response.status_code == 200
    data = response.json()
    params = {p["name"]: p for p in data["parameters"]}

    assert "platform" in params
    assert "style" in params
    assert "video_duration" in params
    assert "topic" in params
    assert "screenplay" in params

@patch("shared.ops.studio.services.job_lifecycle.run_project_task")
def test_run_task(mock_run, client):
    """Test running a task via API (mocked execution)."""
    mock_run.return_value = {"status": "mocked_success"}
    
    response = client.post(
        "/api/run/loan_comparison/smoke_check",
        json={"kwargs": {"foo": "bar"}}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    
    # Check if run_project_task was called in background?
    # TestClient processes background tasks synchronously after request.
    # So mock_run should have been called.
    mock_run.assert_called_once()
    _, call_kwargs = mock_run.call_args
    assert call_kwargs["task_name"] == "smoke_check"
    assert call_kwargs["task_kwargs"] == {"foo": "bar"}


@patch("shared.ops.studio.services.job_lifecycle.run_project_task")
def test_job_status_hydrates_scene_schedule_from_sidecar(mock_run, client, tmp_path: Path):
    sidecar_path = tmp_path / "demo.scene_schedule.json"
    sidecar_path.write_text(
        json.dumps(
            {
                "total_seconds": 6.0,
                "total_frames": 144,
                "scenes": [{"scene_id": "scene_01_hook", "scene_label": "Hook", "pacing_token": "hook_reveal", "mood": "dramatic", "visual_prompt": "高亮对比镜头"}],
                "log_lines": ["scene_schedule :: role=intro :: scene_id=scene_01_hook"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    mock_run.return_value = {
        "final_video_path": str(tmp_path / "demo.mp4"),
        "scene_schedule_path": str(sidecar_path),
    }

    response = client.post(
        "/api/run/loan_comparison/smoke_check",
        json={"kwargs": {}},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    job_response = client.get(f"/api/studio/v1/jobs/{job_id}")
    assert job_response.status_code == 200
    payload = job_response.json()
    assert payload["status"] == "success"
    assert payload["result"]["scene_schedule_path"] == str(sidecar_path)
    assert payload["result"]["scene_schedule"]["scenes"][0]["scene_id"] == "scene_01_hook"
    assert payload["result"]["scene_schedule"]["scenes"][0]["mood"] == "dramatic"
    assert payload["result"]["scene_schedule_download_url"] == f"/api/studio/v1/jobs/{job_id}/scene-schedule"

    download_response = client.get(payload["result"]["scene_schedule_download_url"])
    assert download_response.status_code == 200
    assert "application/json" in download_response.headers["content-type"]


@patch("shared.ops.studio.services.job_lifecycle.run_project_task")
def test_job_status_normalizes_inline_scene_schedule(mock_run, client):
    mock_run.return_value = {
        "scene_schedule": {
            "total_seconds": 6,
            "total_frames": 144,
            "scenes": [{"scene_id": "scene_01_hook", "scene_label": "Hook", "pacing_token": "hook_reveal"}],
        }
    }

    response = client.post(
        "/api/run/loan_comparison/smoke_check",
        json={"kwargs": {}},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    payload = client.get(f"/api/studio/v1/jobs/{job_id}").json()
    assert payload["status"] == "success"
    assert payload["result"]["scene_schedule"]["phases"] == []
    assert payload["result"]["scene_schedule"]["log_lines"] == []
    assert payload["result"]["scene_schedule"]["scenes"][0]["scene_id"] == "scene_01_hook"
    assert payload["result"]["scene_schedule"]["scenes"][0].get("visual_prompt") is None
    assert payload["result"]["scene_schedule_download_url"] == f"/api/studio/v1/jobs/{job_id}/scene-schedule"

    download_response = client.get(payload["result"]["scene_schedule_download_url"])
    assert download_response.status_code == 200
    assert "application/json" in download_response.headers["content-type"]


def test_screenplay_workflow_rejects_projects_without_capability(client):
    response = client.get("/api/screenplay/fund_fee_erosion/providers")
    assert response.status_code == 400
    assert "does not support screenplay workflow" in response.json()["detail"]


def test_intro_project_screenplay_preview_and_edit(client):
    providers_response = client.get("/api/screenplay/video_platform_introduction/providers")
    assert providers_response.status_code == 200
    providers = providers_response.json()
    assert any(provider["name"] == "video_platform_template" for provider in providers)
    # video_platform_template is default when global provider is "mock";
    # otherwise openai_compatible may be default — just verify the provider exists and is enabled
    vpt = [p for p in providers if p["name"] == "video_platform_template"][0]
    assert vpt["enabled"] is True

    preview_response = client.post(
        "/api/screenplay/video_platform_introduction/preview",
        json={
            "payload": {
                "platform": "douyin",
                "style": "tech",
                "topic": "Video Platform Introduction",
                "video_duration": 30,
                "screenplay_provider": "video_platform_template",
            }
        },
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["provider_used"] == "video_platform_template"
    assert preview_payload["screenplay"]["topic"] == "Video Platform Introduction"
    assert len(preview_payload["screenplay"]["scenes"]) >= 4
    first_scene = preview_payload["screenplay"]["scenes"][0]
    assert first_scene["id"].startswith("scene_01_")
    assert "中文短视频创作者" in preview_payload["screenplay"]["logline"]

    updated_title = "平台介绍视频·改稿版"
    updated_narration = "30 秒看懂这个平台，为什么能帮你更快完成介绍视频制作。"
    edit_response = client.patch(
        "/api/screenplay/video_platform_introduction/preview",
        json={
            "payload": {
                "screenplay": preview_payload["screenplay"],
                "screenplay_provider": "video_platform_template",
                "title": updated_title,
                "scene_narration_overrides": {
                    first_scene["id"]: updated_narration,
                },
            }
        },
    )
    assert edit_response.status_code == 200
    edit_payload = edit_response.json()
    assert edit_payload["screenplay"]["title"] == updated_title
    assert edit_payload["changed_scene_ids"] == [first_scene["id"]]
    assert edit_payload["screenplay"]["scenes"][0]["narration"] == updated_narration


def test_http_architecture_manifest(client):
    r = client.get("/api/meta/architecture")
    assert r.status_code == 200
    data = r.json()
    assert data.get("schema_version") == 1
    assert "canonical_prefixes" in data
    assert data["canonical_prefixes"].get("studio_control_plane") == "/api/studio/v1"
    assert "domain_mounts" in data and len(data["domain_mounts"]) >= 1


def test_legacy_paths_redirect_to_studio(client):
    """旧版 /api/agent、/api/jobs 307 到 /api/studio/v1（不跟随重定向，只验 Location）。"""
    r = client.get("/api/jobs", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers.get("location") == "/api/studio/v1/jobs"

    r2 = client.get("/api/jobs?limit=5&offset=0", follow_redirects=False)
    assert r2.status_code == 307
    assert r2.headers.get("location") == "/api/studio/v1/jobs?limit=5&offset=0"

    r3 = client.post("/api/jobs", follow_redirects=False)
    assert r3.status_code == 307
    assert r3.headers.get("location") == "/api/studio/v1/jobs"

    r4 = client.post("/api/agent/compile", follow_redirects=False)
    assert r4.status_code == 307
    assert r4.headers.get("location") == "/api/studio/v1/agent/compile"



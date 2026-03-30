"""真渲染集成测试：用示例剧本 JSON 生成一段测试用 mp4（需 FFmpeg）。

默认不跑（省时间）；只有设置环境变量 VIDEO_PIPELINE_E2E=1 时才执行。说明见 docs/CORE_VIDEO_PIPELINE.md。
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orchestrator.registry import ProjectRegistry
from shared.ops.studio.db.base import reset_engine
from shared.ops.studio.db.init import init_db
from shared.ops.studio.services.job_lifecycle import get_job_public_dict, run_render_job_task, schedule_render_job


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_sample_screenplay() -> dict:
    raw = (_repo_root() / "web" / "sample_screenplay.json").read_text(encoding="utf-8")
    return json.loads(raw)


@pytest.fixture
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dbfile = tmp_path / "studio_video_e2e.db"
    monkeypatch.setenv("STUDIO__DATABASE_URL", f"sqlite:///{dbfile.as_posix()}")
    reset_engine()
    init_db()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.video_e2e
def test_standard_template_screenplay_to_mp4_on_disk(isolated_db: None, tmp_path: Path) -> None:
    """调度器执行 loan_animation：kwargs 含 screenplay + preview + 短时长 → 成片文件存在且非空。"""
    if os.environ.get("VIDEO_PIPELINE_E2E", "").strip() != "1":
        pytest.skip("set environment variable VIDEO_PIPELINE_E2E=1 to run real video render")

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not found on PATH")

    out = tmp_path / "e2e_loan_preview.mp4"
    screenplay = _load_sample_screenplay()

    kwargs: dict = {
        "quality": "preview",
        "duration": 10,
        "screenplay": screenplay,
        "output_file": str(out),
        "loan_amount": 1_000_000,
        "annual_rate": 0.045,
        "loan_years": 30,
    }

    repo_root = _repo_root()
    reg = ProjectRegistry(repo_root / "app")
    reg.discover()
    project = reg.get_project("loan_comparison")
    assert project is not None

    jid = schedule_render_job(project="loan_comparison", task="loan_animation", kwargs=kwargs)
    run_render_job_task(jid, project, "loan_animation", kwargs)

    row = get_job_public_dict(jid)
    assert row is not None, row
    assert row["status"] == "success", row.get("error") or row
    result = row.get("result")
    assert isinstance(result, dict)
    final = result.get("final_video_path")
    assert final, result
    p = Path(final)
    assert p.exists(), final
    assert p.stat().st_size > 0, final


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.video_e2e
def test_http_api_agent_run_produces_mp4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """POST /api/studio/v1/jobs 提交标准模板（含 screenplay）→ Job 成功 → 成片路径存在。"""
    if os.environ.get("VIDEO_PIPELINE_E2E", "").strip() != "1":
        pytest.skip("set environment variable VIDEO_PIPELINE_E2E=1 to run real video render")

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not found on PATH")

    dbfile = tmp_path / "studio_agent_e2e.db"
    monkeypatch.setenv("STUDIO__DATABASE_URL", f"sqlite:///{dbfile.as_posix()}")
    reset_engine()
    init_db()

    out = tmp_path / "e2e_agent_run.mp4"
    body = {
        "schema_version": "1.0",
        "project": "loan_comparison",
        "task": "loan_animation",
        "kwargs": {
            "quality": "preview",
            "duration": 10,
            "screenplay": _load_sample_screenplay(),
            "output_file": str(out),
            "loan_amount": 1_000_000,
            "annual_rate": 0.045,
            "loan_years": 30,
        },
        "intent_summary": "E2E: standardized template + sample_screenplay.json (agent contract)",
    }

    from dashboard import app

    with TestClient(app) as client:
        res = client.post("/api/studio/v1/jobs", json={"template": body})
        assert res.status_code == 200, res.text
        job_id = res.json()["job_id"]

        job = client.get(f"/api/studio/v1/jobs/{job_id}")
        assert job.status_code == 200, job.text
        payload = job.json()
        assert payload["status"] == "success", payload.get("error") or payload
        r = payload.get("result")
        assert isinstance(r, dict)
        final = r.get("final_video_path")
        assert final
        assert Path(final).exists()
        assert Path(final).stat().st_size > 0

"""核心控制面全链路：真实执行任务（无 mock），验收里程碑 M1。

里程碑定义见 docs/CORE_VIDEO_PIPELINE.md。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orchestrator.registry import ProjectRegistry
from shared.studio.db.base import reset_engine
from shared.studio.db.init import init_db
from shared.studio.services.job_lifecycle import get_job_public_dict, run_render_job_task, schedule_render_job


@pytest.fixture
def isolated_studio_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dbfile = tmp_path / "studio_m1.db"
    monkeypatch.setenv("STUDIO__DATABASE_URL", f"sqlite:///{dbfile.as_posix()}")
    reset_engine()
    init_db()


@pytest.mark.integration
def test_m1_real_smoke_check_via_run_render_job_task(isolated_studio_db: None, tmp_path: Path) -> None:
    """调度器 → DB → 真实 run_smoke_check，无 HTTP、无 mock。"""
    repo_root = Path(__file__).resolve().parents[1]
    reg = ProjectRegistry(repo_root)
    reg.discover()
    project = reg.get_project("loan_comparison")
    assert project is not None

    jid = schedule_render_job(project="loan_comparison", task="smoke_check", kwargs={})
    run_render_job_task(jid, project, "smoke_check", {})

    row = get_job_public_dict(jid)
    assert row is not None
    assert row["status"] == "success", row
    result = row.get("result")
    assert isinstance(result, dict)
    assert "equal_interest_total_interest" in result
    assert "equal_principal_total_interest" in result


@pytest.mark.integration
def test_m1_http_post_run_smoke_check_no_mock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """HTTP POST /api/run → BackgroundTasks → 真实 smoke_check → GET /api/jobs/{id} 成功。"""
    # 独立 SQLite，避免与其它用例的默认库互相污染
    dbfile = tmp_path / "studio_http_m1.db"
    monkeypatch.setenv("STUDIO__DATABASE_URL", f"sqlite:///{dbfile.as_posix()}")
    reset_engine()
    init_db()

    from dashboard import app

    with TestClient(app) as client:
        res = client.post(
            "/api/run/loan_comparison/smoke_check",
            json={"kwargs": {}},
        )
        assert res.status_code == 200, res.text
        job_id = res.json()["job_id"]

        job = client.get(f"/api/jobs/{job_id}")
        assert job.status_code == 200, job.text
        payload = job.json()
        assert payload["status"] == "success", payload
        r = payload.get("result")
        assert isinstance(r, dict)
        assert "equal_interest_total_interest" in r

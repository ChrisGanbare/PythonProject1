"""Studio 控制面：独立 SQLite 文件上的建表与任务记录。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.registry import ProjectRegistry
from shared.ops.studio.db.base import reset_engine
from shared.ops.studio.db.init import init_db
from shared.ops.studio.services.job_lifecycle import get_job_public_dict, schedule_render_job


@pytest.fixture
def isolated_studio_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dbfile = tmp_path / "studio_test.db"
    monkeypatch.setenv("STUDIO__DATABASE_URL", f"sqlite:///{dbfile.as_posix()}")
    reset_engine()
    init_db()
    yield
    reset_engine()


def test_schedule_job_persisted(isolated_studio_db: object) -> None:
    jid = schedule_render_job(project="loan_comparison", task="smoke_check", kwargs={})
    row = get_job_public_dict(jid)
    assert row is not None
    assert row["status"] in ("pending", "running", "success", "failed")
    assert row["project"] == "loan_comparison"
    assert row["task"] == "smoke_check"


@patch("shared.ops.studio.services.job_lifecycle.run_project_task")
def test_run_render_updates_db(mock_run, isolated_studio_db: object) -> None:
    mock_run.return_value = {"ok": True}
    reg = ProjectRegistry(Path(__file__).resolve().parents[2] / "app")
    reg.discover()
    project = reg.get_project("loan_comparison")
    assert project is not None

    jid = schedule_render_job(project="loan_comparison", task="smoke_check", kwargs={})
    from shared.ops.studio.services.job_lifecycle import run_render_job_task

    run_render_job_task(jid, project, "smoke_check", {})
    row = get_job_public_dict(jid)
    assert row is not None
    assert row["status"] == "success"
    assert row["result"]["ok"] is True

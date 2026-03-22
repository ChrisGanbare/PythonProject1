"""Project scaffold tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.scaffold import (
    REFERENCE_PROJECT_NAMES,
    _sanitize_project_name,
    delete_project_scaffold,
    generate_project_scaffold,
)
from scheduler import build_parser, scaffold_project


def test_sanitize_project_name() -> None:
    assert _sanitize_project_name("My Project-01") == "my_project_01"


def test_generate_project_scaffold_creates_expected_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "projects").mkdir(parents=True, exist_ok=True)

    project_root = generate_project_scaffold(
        repo_root=repo_root,
        project_name="Demo Project",
        description="Demo description",
    )

    assert project_root.name == "demo_project"
    assert (project_root / "project_manifest.py").exists()
    assert (project_root / "entrypoints.py").exists()
    assert (project_root / "content" / "planner.py").exists()
    assert (project_root / "renderer" / "viz_backend.py").exists()
    assert (project_root / "content" / "sample_screenplay.json").exists()
    manifest_txt = (project_root / "project_manifest.py").read_text(encoding="utf-8")
    assert "viz_backends" in manifest_txt


def test_delete_project_scaffold_removes_directory(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "projects").mkdir(parents=True, exist_ok=True)
    generate_project_scaffold(repo_root=repo_root, project_name="to_delete", description="x")
    root = repo_root / "projects" / "to_delete"
    assert root.is_dir()
    delete_project_scaffold(repo_root, "to_delete")
    assert not root.exists()


def test_delete_project_scaffold_rejects_reference(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "projects" / "loan_comparison").mkdir(parents=True)
    with pytest.raises(PermissionError):
        delete_project_scaffold(repo_root, "loan_comparison")


def test_generate_project_scaffold_rejects_duplicate(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "projects" / "demo_project").mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileExistsError):
        generate_project_scaffold(repo_root=repo_root, project_name="demo_project")


def test_scheduler_parser_supports_scaffold_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["scaffold", "--name", "demo_project", "--description", "Demo", "--port", "8123"])

    assert args.command == "scaffold"
    assert args.name == "demo_project"
    assert args.description == "Demo"
    assert args.port == 8123


def test_scaffold_project_returns_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    created_paths: list[Path] = []

    def fake_generate(repo_root: Path, project_name: str, description: str | None, port: int) -> Path:
        del repo_root, description, port
        path = tmp_path / project_name
        created_paths.append(path)
        return path

    monkeypatch.setattr("scheduler.generate_project_scaffold", fake_generate)

    exit_code = scaffold_project("demo_project", "Demo", 8123)

    assert exit_code == 0
    assert created_paths == [tmp_path / "demo_project"]


"""Tests for Agent catalog / validate (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from orchestrator.registry import ProjectRegistry
from shared.ai.agent.catalog import build_agent_catalog
from shared.ai.agent.schemas import StandardVideoJobRequest
from shared.ai.agent.validate import validate_standard_request

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def registry() -> ProjectRegistry:
    r = ProjectRegistry(REPO / "app")
    r.discover()
    return r


def test_build_agent_catalog_contains_loan_tasks(registry: ProjectRegistry) -> None:
    cat = build_agent_catalog(registry)
    names = {p["name"] for p in cat["projects"]}
    assert "loan_comparison" in names
    loan = next(p for p in cat["projects"] if p["name"] == "loan_comparison")
    task_names = {t["name"] for t in loan["tasks"]}
    assert "loan_animation" in task_names
    anim = next(t for t in loan["tasks"] if t["name"] == "loan_animation")
    assert "parameters" in anim


def test_validate_ok(registry: ProjectRegistry) -> None:
    req = StandardVideoJobRequest(
        project="loan_comparison",
        task="smoke_check",
        kwargs={},
        intent_summary="test",
    )
    v = validate_standard_request(req, registry)
    assert v.valid
    assert not v.errors


def test_validate_bad_project(registry: ProjectRegistry) -> None:
    req = StandardVideoJobRequest(project="nope", task="smoke_check", kwargs={})
    v = validate_standard_request(req, registry)
    assert not v.valid
    assert any("nope" in e for e in v.errors)


def test_standard_request_forbids_extra() -> None:
    with pytest.raises(Exception):
        StandardVideoJobRequest.model_validate(
            {
                "schema_version": "1.0",
                "project": "loan_comparison",
                "task": "smoke_check",
                "kwargs": {},
                "extra_field": 1,
            }
        )


def test_schema_json_has_required_fields() -> None:
    s = StandardVideoJobRequest.model_json_schema()
    assert "properties" in s
    assert "project" in s["properties"]
    assert "task" in s["properties"]
    assert "kwargs" in s["properties"]

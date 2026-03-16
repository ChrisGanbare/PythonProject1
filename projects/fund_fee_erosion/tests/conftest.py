"""Pytest shared fixtures for fund_fee_erosion project."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Make shared/ and projects/ importable when running tests directly
_workspace_root = Path(__file__).resolve().parents[3]
_projects_root  = Path(__file__).resolve().parents[2]
for _p in [str(_workspace_root), str(_projects_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.config.settings import Settings
from fund_fee_erosion.models.calculator import FundParams


@pytest.fixture(scope="session")
def temp_dir() -> Path:
    path = Path(tempfile.mkdtemp(prefix="test_fund_"))
    yield path
    if path.exists():
        shutil.rmtree(path)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    return Settings(
        debug=True,
        video__output_dir=temp_dir / "outputs",
        cache_dir=temp_dir / "cache",
        temp_dir=temp_dir / "temp",
        log__log_dir=temp_dir / "logs",
    )


@pytest.fixture
def default_params() -> FundParams:
    return FundParams(principal=1_000_000, gross_return=0.08, years=30)

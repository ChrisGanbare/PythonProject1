"""Pytest shared fixtures."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile

import pytest

_workspace_root = Path(__file__).resolve().parents[1]
_projects_root = _workspace_root / "projects"
for _p in [str(_projects_root), str(_workspace_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.config.settings import Settings
from loan_comparison.models.loan import LoanData


@pytest.fixture(scope="session")
def temp_dir() -> Path:
    path = Path(tempfile.mkdtemp(prefix="test_video_"))
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
def loan_data() -> LoanData:
    return LoanData(
        loan_amount=1_000_000,
        annual_rate=0.045,
        loan_years=30,
    )

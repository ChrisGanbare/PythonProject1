"""
Pytest 配置和全局 fixture
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from config.settings import Settings


@pytest.fixture(scope="session")
def temp_dir():
    """临时目录（会话级别）"""
    temp_path = Path(tempfile.mkdtemp(prefix="test_video_"))
    yield temp_path
    # 清理
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def test_settings(temp_dir):
    """测试配置"""
    # 创建临时配置
    settings = Settings(
        debug=True,
        video__output_dir=temp_dir / "outputs",
        cache_dir=temp_dir / "cache",
        temp_dir=temp_dir / "temp",
        log__log_dir=temp_dir / "logs",
    )
    return settings


@pytest.fixture
def loan_data():
    """贷款数据 fixture"""
    from models.loan import LoanData
    
    return LoanData(
        loan_amount=1_000_000,
        annual_rate=0.045,
        loan_years=30,
    )


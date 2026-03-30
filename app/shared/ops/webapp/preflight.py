"""上线前自检（业务落地）：依赖、成片必备条件、Studio 库目录可写。"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class CheckItem(NamedTuple):
    name: str
    ok: bool
    detail: str
    critical: bool


def _repo_root() -> Path:
    # app/shared/ops/webapp/preflight.py → parents[4] = workspace root
    return Path(__file__).resolve().parents[4]


def run_preflight() -> tuple[list[CheckItem], bool]:
    """返回 (条目列表, 是否全部关键项通过)。"""
    root = _repo_root()
    items: list[CheckItem] = []

    # FFmpeg — 成片 / 快速图表视频
    ff = shutil.which("ffmpeg")
    items.append(
        CheckItem(
            "FFmpeg（成片与图表视频）",
            ff is not None,
            ff or "未在 PATH 中找到 ffmpeg，请安装并配置环境变量",
            critical=True,
        )
    )

    for mod, label, critical in (
        ("fastapi", "FastAPI", True),
        ("uvicorn", "Uvicorn", True),
        ("sqlalchemy", "SQLAlchemy（Studio 作业库）", True),
        ("plotly", "Plotly（图表渲染）", True),
        ("openai", "openai 包（可选，AI 编译/部分剧本）", False),
    ):
        try:
            __import__(mod)
            items.append(CheckItem(label, True, "已安装", critical=critical))
        except ImportError:
            items.append(
                CheckItem(
                    label,
                    not critical,
                    f"未安装: pip 安装 requirements 中的依赖",
                    critical=critical,
                )
            )

    # Studio 数据库父目录可写
    try:
        from shared.ops.studio.config import get_database_url, is_sqlite

        url = get_database_url()
        if is_sqlite(url):
            # sqlite:///path
            path_part = url.replace("sqlite:///", "", 1).split("?", 1)[0]
            db_path = Path(path_part)
            parent = db_path.parent
            parent.mkdir(parents=True, exist_ok=True)
            test_file = parent / ".write_test"
            try:
                test_file.write_text("ok", encoding="utf-8")
                test_file.unlink(missing_ok=True)
                items.append(
                    CheckItem(
                        "Studio 数据库目录可写",
                        True,
                        str(parent),
                        critical=True,
                    )
                )
            except OSError as e:
                items.append(
                    CheckItem(
                        "Studio 数据库目录可写",
                        False,
                        str(e),
                        critical=True,
                    )
                )
        else:
            items.append(
                CheckItem(
                    "Studio 数据库",
                    True,
                    f"非 SQLite：{url[:60]}...",
                    critical=True,
                )
            )
    except Exception as e:
        items.append(
            CheckItem("Studio 数据库配置", False, str(e), critical=True)
        )

    # 首页静态资源（前端目录 web/）
    idx = root / "web" / "index.html"
    items.append(
        CheckItem(
            "控制台首页 web/index.html",
            idx.is_file(),
            str(idx) if idx.is_file() else "文件缺失",
            critical=True,
        )
    )

    # OpenCV — 部分领域子应用挂载（非阻断主控制台）
    try:
        import cv2  # noqa: F401

        items.append(CheckItem("OpenCV（可选，部分领域 API）", True, "已安装", critical=False))
    except ImportError:
        items.append(
            CheckItem(
                "OpenCV（可选）",
                True,
                "未安装：主控制台仍可用；部分 /api/domain/* 子应用可能跳过挂载",
                critical=False,
            )
        )

    all_critical_ok = all(i.ok for i in items if i.critical)
    return items, all_critical_ok


def print_report_and_exit() -> int:
    print("环境自检（业务落地）")
    print("=" * 50)
    items, ok = run_preflight()
    for it in items:
        mark = "✓" if it.ok else "✗"
        crit = "[必需] " if it.critical else "[可选] "
        print(f"  {mark} {crit}{it.name}")
        if not it.ok or (it.ok and len(it.detail) < 120 and it.detail not in ("已安装",)):
            print(f"      {it.detail}")
    print("=" * 50)
    if ok:
        print("结论：关键项通过，可启动服务（python main.py dashboard）。")
        return 0
    print("结论：存在阻塞项，请先处理上述 ✗ [必需] 项后再启动。")
    return 1


if __name__ == "__main__":
    sys.exit(print_report_and_exit())

from __future__ import annotations

import atexit
import errno
import logging
import os
import signal
import sys
import time
from contextlib import suppress as contextlib_suppress
from pathlib import Path

# 添加 app/ 及 app/projects/ 到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # app/scripts/ → app/ → root
_APP_DIR = PROJECT_ROOT / "app"
PROJECTS_DIR = _APP_DIR / "projects"
for _p in (_APP_DIR, PROJECTS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shared.ops.studio.api.control_plane import create_v1_router
from shared.ops.webapp.domain_mounts import mount_domain_apps
from shared.ops.webapp.lifespan import lifespan
from shared.ops.webapp.routers.legacy_redirects import router as legacy_redirects_router
from shared.ops.webapp.routers.meta import router as meta_router
from shared.ops.webapp.routers.pages import STATIC_DIR, router as pages_router
from shared.ops.webapp.routers.projects import router as projects_router
from shared.ops.webapp.routers.screenplay_proxy import router as screenplay_proxy_router
from shared.ops.webapp.routers.settings import router as settings_router
from shared.ops.webapp.state import REPO_ROOT, registry

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

sys.path.append(str(REPO_ROOT / "app" / "projects"))

app = FastAPI(
    title="Video Project Control Center",
    lifespan=lifespan,
    description=(
        "统一 HTTP 入口。权威前缀："
        "`/api/studio/v1`（作业/会话/Agent）、"
        "`/api/video/v2`（快速图表视频）、"
        "`/api/domain/{project}`（领域子应用挂载）。"
        " 架构清单：`GET /api/meta/architecture`。"
    ),
)

# Studio 控制面（作业 / 会话 / Agent）；勿与已废弃的根 Video v1 混淆
app.include_router(create_v1_router(lambda: registry), prefix="/api/studio/v1")

app.include_router(legacy_redirects_router)

# 快速图表视频（真实渲染：core.v2_renderer）
try:
    from api.v2_routes import router as v2_router

    app.include_router(v2_router)
    logger.info("Quick video API registered at /api/video/v2")
except Exception as e:
    logger.warning("Failed to register quick video API routes: %s", e)

mount_domain_apps(app, logger=logger)

app.include_router(meta_router)
app.include_router(pages_router)
app.include_router(settings_router)
app.include_router(projects_router)
app.include_router(screenplay_proxy_router)

# Mount static assets after all API routes so `/api/...` is never captured by the static app.
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _is_address_in_use(exc: OSError) -> bool:
    if exc.errno == errno.EADDRINUSE:
        return True
    # Windows: 通常只有 winerror，errno 可能为 0
    return getattr(exc, "winerror", None) == 10048


# PID 文件：运行时目录，gitignore 已覆盖
_PID_FILE = REPO_ROOT / "runtime" / "dashboard.pid"


def _stop_previous_instance() -> None:
    """若 PID 文件存在且对应进程仍在运行，终止它并等待端口释放。"""
    if not _PID_FILE.exists():
        return
    try:
        old_pid = int(_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        with contextlib_suppress(OSError):
            _PID_FILE.unlink()
        return
    if old_pid == os.getpid():
        return
    try:
        os.kill(old_pid, 0)  # 探测：进程不存在时抛 OSError
    except (OSError, SystemError):
        return  # 进程已不存在，残留 PID 文件，直接忽略
    logger.info("Stopping previous dashboard instance (PID %d) ...", old_pid)
    try:
        os.kill(old_pid, signal.SIGTERM)  # Windows 等同于 TerminateProcess
        for _ in range(30):  # 最多等待 3 秒
            time.sleep(0.1)
            try:
                os.kill(old_pid, 0)
            except OSError:
                break  # 进程已退出
        else:
            logger.warning("Previous instance (PID %d) did not exit within 3 s.", old_pid)
    except OSError:
        pass


def _register_pid_file() -> None:
    """写入当前进程 PID，atexit 时自动删除。"""
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: _PID_FILE.unlink(missing_ok=True))


def run_dashboard() -> None:
    """Console entry (`video-dashboard` after `pip install -e .`)."""
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8090"))
    _stop_previous_instance()  # 自动停止上一个实例
    _register_pid_file()  # 记录本次 PID
    print(f"Starting Video Control Center on http://{host}:{port} ...")
    try:
        uvicorn.run(app, host=host, port=port)
    except OSError as exc:
        if _is_address_in_use(exc):
            print(
                f"端口 {port} 仍被占用（等待超时），请手动关闭后重试，"
                f"或设置环境变量 DASHBOARD_PORT 使用其他端口。",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    run_dashboard()

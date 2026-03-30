"""
统一 HTTP 入口（与 Dashboard 共用同一 FastAPI 应用）。

已移除旧版「Video API v1」（/api/v1/templates|themes|jobs 占位实现）。
请使用：

- ``/api/studio/v1/*`` — Studio 控制面（作业、会话、Agent）
- ``/api/video/v2/*`` — 快速图表视频
- ``/api/domain/<project>/*`` — 领域 HTTP（由原各子项目 FastAPI 挂载）

启动::

    python main.py api --host 0.0.0.0 --port 8000
    python -m api.main --port 8000
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# app/api/ → app/ → root
_ROOT = Path(__file__).resolve().parent.parent.parent
_APP = _ROOT / "app"
for _p in (_APP, _APP / "projects"):
    s = str(_p)
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="PythonProject1 unified API (same app as Dashboard)")
    parser.add_argument("--host", default=os.environ.get("API_HOST", "0.0.0.0"), help="监听地址")
    parser.add_argument("--port", type=int, default=int(os.environ.get("API_PORT", "8000")), help="端口")
    parser.add_argument("--reload", action="store_true", help="开发热重载")
    args = parser.parse_args()

    # 与 Dashboard 相同应用；API-only 时可跳过部分静态资源行为（应用本身仍含页面路由）
    os.environ.setdefault("DASHBOARD_HOST", args.host)
    os.environ.setdefault("DASHBOARD_PORT", str(args.port))

    print(f"统一 API 服务 {args.host}:{args.port}（与 Dashboard 同源应用）")
    print("OpenAPI: http://{}:{}/docs".format(args.host, args.port))
    uvicorn.run(
        "scripts.dashboard:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

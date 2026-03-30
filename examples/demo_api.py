#!/usr/bin/env python3
"""
演示：通过统一控制台提供的 HTTP API 创建视频（无旧版 /api/v1/jobs）。

先启动::

    python main.py dashboard
    # 默认 http://127.0.0.1:8090

再运行本脚本或直接使用 curl::

    curl -X POST "http://127.0.0.1:8090/api/video/v2/create" \\
      -H "Content-Type: application/json" \\
      -d '{
        "template": {"template_id": "bar_chart_race", "template_name": "柱状图竞赛"},
        "data": {
          "input_mode": "manual",
          "labels": "2024-01,2024-02,2024-03",
          "values": "100,150,200",
          "series_name": "销售额"
        },
        "brand": {"brand_id": "corporate"},
        "platform": "bilibili"
      }'

    curl "http://127.0.0.1:8090/api/video/v2/status/{job_id}"
    curl "http://127.0.0.1:8090/api/video/v2/download/{job_id}" -o output.mp4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _request_json(method: str, url: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return e.code, err_body
    except URLError as e:
        print(f"请求失败: {e}", file=sys.stderr)
        return 0, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick video API demo (unified dashboard)")
    parser.add_argument("--base", default="http://127.0.0.1:8090", help="Dashboard 根 URL")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    print("1) POST /api/video/v2/create")
    status, created = _request_json(
        "POST",
        f"{base}/api/video/v2/create",
        {
            "template": {"template_id": "bar_chart_race", "template_name": "柱状图竞赛"},
            "data": {
                "input_mode": "manual",
                "labels": "2024-01,2024-02,2024-03",
                "values": "100,150,200",
                "series_name": "销售额",
            },
            "brand": {"brand_id": "corporate"},
            "platform": "bilibili",
        },
    )
    print(f"   HTTP {status}: {created}")
    if status != 200 or not isinstance(created, dict):
        return 1
    job_id = created.get("job_id")
    if not job_id:
        return 1

    print(f"\n2) 轮询 GET /api/video/v2/status/{job_id}")
    for i in range(60):
        time.sleep(1)
        st, payload = _request_json("GET", f"{base}/api/video/v2/status/{job_id}")
        if st != 200 or not isinstance(payload, dict):
            print(f"   [{i}] HTTP {st}: {payload}")
            continue
        print(f"   [{i}] {payload.get('status')} progress={payload.get('progress')}")
        if payload.get("status") == "completed":
            print(f"\n3) 下载 GET /api/video/v2/download/{job_id}")
            dl, _ = _request_json("GET", f"{base}/api/video/v2/download/{job_id}")
            print(f"   (请用浏览器或 curl -o 保存文件；此处仅检查是否可访问，HTTP {dl})")
            return 0
        if payload.get("status") == "failed":
            print("   失败:", payload.get("error"))
            return 1

    print("超时未完成")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

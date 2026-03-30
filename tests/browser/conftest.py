"""启动真实 dashboard 进程，供 Playwright 连接（模拟浏览器操作）。"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="session")
def dashboard_live_url() -> str:
    """本会话内启动一次 uvicorn，返回根 URL（无尾部斜杠）。"""
    port = _free_port()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "dashboard:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 45.0
    last_err = None
    while time.time() < deadline:
        if proc.poll() is not None:
            err = proc.stderr.read() if proc.stderr else ""
            pytest.fail(f"dashboard 进程已退出: {err[:2000]}")
        try:
            r = requests.get(f"{base}/", timeout=1.0)
            if r.status_code == 200:
                yield base
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return
        except Exception as e:
            last_err = e
            time.sleep(0.3)
    proc.terminate()
    pytest.fail(f"无法在超时内连上 dashboard: {base} last_err={last_err!r}")


@pytest.fixture
def playwright_page(dashboard_live_url: str):
    """单测内 Chromium 页；未安装 playwright 时整条用例跳过。"""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as exc:
            pytest.skip(
                "未检测到 Chromium（请执行：python -m playwright install chromium）。"
                f" 原始错误: {exc}"
            )
        page = browser.new_page()
        page.set_default_timeout(25_000)
        try:
            yield page, dashboard_live_url
        finally:
            browser.close()

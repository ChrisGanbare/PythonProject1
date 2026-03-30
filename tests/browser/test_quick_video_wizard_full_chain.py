"""单机 / 内网控制台场景：首页向导 → POST /api/video/v2/create → 轮询直至「视频生成成功」。

默认跳过（避免 CI/无 ffmpeg 环境耗时失败）：
  set VIDEO_UI_E2E=1
  需 ffmpeg 在 PATH，且已安装 Playwright Chromium。

运行：
  pip install -r requirements-e2e-ui.txt && python -m playwright install chromium
  set VIDEO_UI_E2E=1
  pytest tests/e2e_browser/test_quick_video_wizard_full_chain.py -m "browser and video_ui_e2e" -v --tb=short
"""

from __future__ import annotations

import os
import shutil

import pytest


@pytest.mark.browser
@pytest.mark.video_ui_e2e
@pytest.mark.slow
def test_quick_video_wizard_end_to_end_success(playwright_page):
    """全链路：点击开始生成 → 等待成功横幅（真渲染，可能 1～5 分钟）。"""
    if os.environ.get("VIDEO_UI_E2E", "").strip() != "1":
        pytest.skip("set VIDEO_UI_E2E=1 to run real chart video render from UI")

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not found on PATH")

    page, base = playwright_page
    page.set_default_timeout(360_000)

    page.goto(f"{base}/")
    page.locator(".template-card").first.click()
    page.get_by_role("button", name="下一步").click()

    page.get_by_placeholder("例如：2024-01, 2024-02, 2024-03").fill("2024-01,2024-02")
    page.get_by_placeholder("例如：100, 150, 200").fill("10,20")
    page.get_by_role("button", name="下一步").click()

    page.locator(".brand-badge").first.click()
    page.get_by_role("button", name="下一步").click()

    with page.expect_response("**/api/video/v2/create", timeout=120_000) as resp_info:
        page.get_by_role("button", name="开始生成").click()

    resp = resp_info.value
    assert resp.ok, f"create failed: {resp.status} {resp.text()[:500]}"

    page.get_by_text("视频生成成功", exact=False).first.wait_for(state="visible", timeout=360_000)

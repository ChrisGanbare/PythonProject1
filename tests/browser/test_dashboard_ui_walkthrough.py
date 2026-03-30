"""用 Playwright 模拟真人操作首页（快速图表向导），与当前 static/index.html 对齐。

前置：
  pip install -r requirements-e2e-ui.txt
  python -m playwright install chromium

运行：
  pytest tests/e2e_browser -m browser -v
"""

from __future__ import annotations

import pytest


@pytest.mark.browser
def test_home_loads_wizard_title(playwright_page):
    """首页展示 v2.3 向导标题（Vue 已挂载）。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.wait_for_load_state("domcontentloaded")
    page.get_by_text("PythonProject1 v2.3", exact=False).first.wait_for(state="visible", timeout=20_000)


@pytest.mark.browser
def test_open_global_settings_modal(playwright_page):
    """顶栏齿轮打开「全局设置」模态框。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.get_by_title("全局设置").click()
    page.locator("#settingsModal").get_by_text("全局设置", exact=True).first.wait_for(
        state="visible", timeout=10_000
    )
    page.keyboard.press("Escape")


@pytest.mark.browser
def test_wizard_navigate_to_generate_step(playwright_page):
    """向导 1→2→3→4：选模板、填数据、选品牌，出现「开始生成」。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.locator(".template-card").first.click()
    page.get_by_role("button", name="下一步").click()

    page.get_by_placeholder("例如：2024-01, 2024-02, 2024-03").fill("2024-01,2024-02")
    page.get_by_placeholder("例如：100, 150, 200").fill("10,20")
    page.get_by_role("button", name="下一步").click()

    page.locator(".brand-badge").first.click()
    page.get_by_role("button", name="下一步").click()

    page.get_by_role("button", name="开始生成").wait_for(state="visible", timeout=10_000)
    page.get_by_text("确认配置", exact=False).wait_for(state="visible", timeout=5_000)

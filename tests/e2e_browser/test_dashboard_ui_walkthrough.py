"""用 Playwright 模拟真人操作控制台页面，发现纯 API 测试覆盖不到的交互问题。

前置：
  pip install -e ".[uat]"
  playwright install chromium

运行：
  pytest tests/e2e_browser -m browser -v
"""

from __future__ import annotations

import pytest


@pytest.mark.browser
def test_home_loads_and_shows_console_title(playwright_page):
    """打开首页，应看到侧栏标题（Vue 已挂载）。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.wait_for_load_state("domcontentloaded")
    expect = page.get_by_text("创作控制台", exact=False)
    expect.first.wait_for(state="visible", timeout=20_000)


@pytest.mark.browser
def test_open_usage_guide_modal(playwright_page):
    """顶栏「使用说明」可点开模态框。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.get_by_role("button", name="使用说明").click()
    page.get_by_role("heading", name="控制台使用说明").wait_for(state="visible", timeout=10_000)
    page.keyboard.press("Escape")


@pytest.mark.browser
def test_switch_sidebar_to_intent_sessions(playwright_page):
    """侧栏可切换到「意图会话」分区。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.get_by_role("button", name="意图会话").click()
    # 新建会话按钮应对可见（分区切换成功）
    page.get_by_role("button", name="新建会话").wait_for(state="visible", timeout=10_000)


@pytest.mark.browser
def test_global_settings_opens_modal(playwright_page):
    """全局设置按钮能打开设置对话框（标题为「全局配置」）。"""
    page, base = playwright_page
    page.goto(f"{base}/")
    page.get_by_role("button", name="全局设置").click()
    page.get_by_role("heading", name="全局配置").wait_for(state="visible", timeout=10_000)
    page.keyboard.press("Escape")

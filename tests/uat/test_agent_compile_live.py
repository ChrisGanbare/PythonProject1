"""真实 Agent（OpenAI 兼容接口）调用 /api/agent/compile 的 UAT。

这不是默认 CI 测试：需要本机 .env 已配置密钥，并显式打开开关。

  PowerShell:
    $env:UAT_AGENT_COMPILE = "1"
    pytest tests/uat -m agent_uat -v

与「浏览器点击」分离：这里只验证**编译接口**在真模型下能否返回可用标准模板。
浏览器全链路仍需人工或 Playwright 在页面里粘贴编译结果再点运行。
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from dashboard import app


@pytest.mark.agent_uat
def test_compile_natural_language_returns_template():
    if os.environ.get("UAT_AGENT_COMPILE", "").strip() != "1":
        pytest.skip("设置环境变量 UAT_AGENT_COMPILE=1 以启用真实 Agent 编译 UAT")

    from shared.config.settings import settings

    if not (settings.api.openai_compatible_api_key and str(settings.api.openai_compatible_api_key).strip()):
        pytest.skip(".env 中未配置 openai_compatible_api_key，无法调用真实模型")

    body = {
        "prompt": (
            "请生成一条可执行的标准视频任务：项目 loan_comparison，任务 loan_animation，"
            "画质 preview，时长约15秒，抖音竖屏。只输出合法 JSON 模板所需字段。"
        ),
        "persist_turns": False,
    }

    with TestClient(app) as client:
        res = client.post("/api/agent/compile", json=body)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data.get("success") is True, data
        std = data.get("standard_request")
        assert std is not None, data
        assert std.get("project"), "模板里应有 project"
        assert std.get("task"), "模板里应有 task"
        assert isinstance(std.get("kwargs"), dict)

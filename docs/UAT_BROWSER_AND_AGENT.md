# UAT：真实 Agent + 浏览器操作（备忘）

详细说明以你在对话里收到的解释为准；本文只列命令，避免重复长文。

## 1. 真实 Agent（编译接口）

- **测什么**：本机 `.env` 已填 OpenAI 兼容密钥时，`POST /api/agent/compile` 能否返回可用标准模板。  
- **命令**：

```powershell
$env:UAT_AGENT_COMPILE = "1"
pytest tests/uat -m agent_uat -v
```

## 2. 模拟浏览器点击（Playwright）

- **测什么**：首页加载、使用说明、侧栏分区、全局设置等**只有真人点页面才会暴露**的问题（与 `TestClient` 测 API 不同）。  
- **安装**：

```powershell
pip install -e ".[uat]"
python -m playwright install chromium
```

- **命令**：

```powershell
pytest tests/e2e_browser -m browser -v
```

未安装 Chromium 时，相关用例会**自动跳过**并提示安装命令，不会报错退出。

## 3. 与「全链路成片」的关系

- 浏览器 UAT 侧重 **UI 交互**；`VIDEO_PIPELINE_E2E=1` 侧重 **真生成 mp4**。  
- 真实 Agent UAT 侧重 **模型能否产出可执行模板**；若要页面里粘贴结果再跑成片，需另做用例或人工点控制台。

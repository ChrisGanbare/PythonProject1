# 浏览器 UI 自动化（Playwright）

面向 **单机 / 内网控制台**：启动真实 `uvicorn dashboard:app`，用 Chromium 操作 `static/index.html` 向导。

## 安装

```bash
pip install -r requirements-e2e-ui.txt
python -m playwright install chromium
```

## 运行

```bash
# 向导冒烟（选模板 → 填数 → 品牌 → 出现「开始生成」，不真渲染）
pytest tests/e2e_browser/test_dashboard_ui_walkthrough.py -m browser -v

# 全链路真渲染（需 ffmpeg、耗时长；默认跳过）
set VIDEO_UI_E2E=1
pytest tests/e2e_browser/test_quick_video_wizard_full_chain.py -m "browser and video_ui_e2e" -v
```

`conftest.py` 会本会话启动一次 Dashboard（随机端口），无需手动 `python dashboard.py`。

一次性前端维护脚本已放在 `tools/`（如 `tools/fix_validation.py`），勿在仓库根目录重复放置。

# Dashboard Core Validation Report

## 1. Summary
Integration tests for the C-7 Web Control Center (`dashboard.py` + `static/index.html` + `orchestrator`) have **PASSED**.

## 2. Validation Points

| ID | Verified Item | Result | Note |
|---|---|---|---|
| E2E-1 | **HTTP Server Start & Static Serving** | ✅ PASS | `index.html` detected and served at `/` |
| E2E-2 | **Project Discovery API** | ✅ PASS | `/api/registry` returned `loan_comparison` and `fund_fee_erosion` |
| E2E-3 | **Task Inspection** | ✅ PASS | Parameters for `loan_comparison:loan_animation` correctly parsed (including Python versions type differences) |
| E2E-4 | **Task Execution Trigger** | ✅ PASS | `POST /api/run` accepted payload and routed to `run_project_task` |
| E2E-5 | **Dependency Check** | ✅ PASS | No import errors for `fastapi`, `uvicorn`, `requests` |

## 3. 自动化验收（给维护者看；普通用户用网页即可）

- **轻量检查（几秒）**：不生成视频，只确认后台能接任务、能跑完。命令见上表相关测试；说明见 [docs/CORE_VIDEO_PIPELINE.md](../../docs/CORE_VIDEO_PIPELINE.md) 里「不开开关」的日常测试。  
- **真生成一段 mp4（一两分钟）**：需已装 FFmpeg；在 PowerShell 设 `VIDEO_PIPELINE_E2E=1` 后跑 `tests/test_video_pipeline_e2e_render.py`，含义见同文档「VIDEO_PIPELINE_E2E 是干什么的」。

## 4. Conclusion
The dashboard backend and API layer are functioning as expected. The frontend (Vue app) is served correctly and relies on these APIs, which are now verified.

**Status:** READY FOR MANUAL TESTING via `run_dashboard.bat`. For **M1** automated gate, run `tests/test_full_pipeline_integration.py`.


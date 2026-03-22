# loan_comparison screenplay API

本项目已接入第一阶段的 **编剧（Screenplay）→ 导演（Director）→ 渲染（Renderer）** 架构。

## 当前已支持

- 可插拔 screenplay provider 架构
- 内置 `mock` provider
- 可选 `openai_compatible` provider（配置后自动启用）
- 剧本预览接口
- 剧本修改接口
- 原有视频生成接口保持兼容

## 新增接口

### 1. 列出可用编剧 provider

`GET /api/screenplay/providers`

### 2. 生成剧本预览

`POST /api/screenplay/preview`

示例请求：

```json
{
  "platform": "douyin",
  "style": "tech",
  "loan_amount": 1000000,
  "annual_rate": 0.045,
  "loan_years": 30,
  "topic": "房贷利息真相",
  "screenplay_provider": "mock"
}
```

### 3. 修改剧本

`PATCH /api/screenplay/preview`

示例请求：

```json
{
  "screenplay": {"title": "...", "scenes": []},
  "title": "房贷利息真相｜二次改稿",
  "scene_narration_overrides": {
    "scene_01_hook": "新的开场钩子文案"
  }
}
```

## Provider 配置

位于 `shared/config/settings.py`：

- `screenplay_provider_default`
- `screenplay_provider_fallback`
- `screenplay_enabled_providers`
- `screenplay_allow_provider_override`
- `openai_compatible_base_url`
- `openai_compatible_api_key`
- `openai_compatible_model`

## 快速验证

```powershell
python -m pytest "D:\pythonProject\video_project\projects\loan_comparison\tests\test_api.py" -q
```


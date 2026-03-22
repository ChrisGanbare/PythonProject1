"""Code Studio：自然语言 → 项目代码补丁 via OpenAI-compatible Chat API."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from shared.code_studio.schemas import CodeCompilePatch, CodeCompileResponse
from shared.config.settings import settings

logger = logging.getLogger(__name__)

# 每个项目默认读取并注入上下文的文件（相对 project_root）
_CONTEXT_FILES = [
    "project_manifest.py",
    "entrypoints.py",
    "renderer/viz_backend.py",
    "models/loan.py",  # loan_comparison 特有
    "models/fund.py",  # fund_fee_erosion 特有
]

_PATCH_SCHEMA = """
interface CodePatch {
  file_path: string;   // 相对 project_root，如 "renderer/viz_backend.py"
  new_content: string; // 文件完整新内容（整体替换，非 diff）
  explanation: string; // 简要中文说明，≤120字
}
"""

_PLATFORM_NOTE = """\
平台规格约束（强制遵守，不得更改）：
| 平台                  | 分辨率      | FPS |
|-----------------------|-------------|-----|
| douyin                | 1080×1920   | 30  |
| bilibili_landscape    | 1920×1080   | 60  |
| bilibili_portrait     | 1080×1920   | 60  |
| xiaohongshu           | 1080×1350   | 30  |

渲染器约束：
- _draw_frame(frame_idx, total_frames, width, height, dpi) 函数签名不可改变
- render_video(quality, platform, output_file) 函数签名不可改变
- 继续支持断点续帧逻辑（跳过已存在的帧文件）
"""


def _build_system_prompt(file_context: str, previous_turns_text: str) -> str:
    hist_section = ""
    if previous_turns_text.strip():
        hist_section = f"\n\n【历史对话记录（最近若干轮）】\n{previous_turns_text}\n"
    return f"""你是「Code Studio 代码工坊」的 AI 编程助手，专为数据可视化视频制作项目提供精准代码修改服务。
你的唯一输出必须是**一个合法的 JSON 对象**（不要 markdown 代码块包裹，不要解释文字），符合下方 TypeScript 接口：

{_PATCH_SCHEMA}

{_PLATFORM_NOTE}

当前项目代码上下文：
{file_context}
{hist_section}
规则：
1. new_content 必须是完整的、可直接写入磁盘的文件文本；不要省略无关代码。
2. file_path 必须是相对 project_root 的路径，与上下文中的文件名对应。
3. 一次只修改**一个文件**；若用户需求涉及多文件，优先修改最核心的那个并在 explanation 中注明其余建议。
4. 若用户需求在已有代码中已实现，直接返回解释说明（new_content 仍需包含完整文件内容，不做修改）。
5. 不要重新发明已有 import；遵守文件顶部已有的依赖。
6. 不要输出任何 JSON 以外的内容。
"""


def _read_project_files(project_root: Path) -> str:
    """读取项目关键文件，拼接为上下文字符串（超长文件截断到 8000 字符）。"""
    parts: list[str] = []
    for rel in _CONTEXT_FILES:
        p = project_root / rel
        if not p.exists():
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if len(content) > 8000:
            content = content[:8000] + "\n...[文件内容已截断]..."
        parts.append(f"### {rel}\n```python\n{content}\n```")
    if not parts:
        return "（未找到可读文件）"
    return "\n\n".join(parts)


def _turns_to_history_text(previous_turns: list[dict[str, Any]]) -> str:
    """将历史轮次列表转为可读对话文本（最近 6 轮，避免超长 context）。"""
    if not previous_turns:
        return ""
    recent = previous_turns[-6:]
    lines: list[str] = []
    for t in recent:
        role = t.get("role", "?")
        role_label = "用户" if role == "user" else "助手"
        text = t.get("content_text") or ""
        file_path = t.get("file_path") or ""
        if file_path:
            text += f"\n  [修改文件: {file_path}]"
        lines.append(f"[{role_label}] {text}")
    return "\n".join(lines)


def compile_code_request(
    prompt: str,
    project_root: Path,
    *,
    previous_turns: list[dict[str, Any]] | None = None,
    file_hint: str | None = None,
) -> CodeCompileResponse:
    """根据自然语言需求为指定项目生成代码补丁。

    Args:
        prompt: 用户的自然语言代码需求
        project_root: 项目根目录（绝对路径）
        previous_turns: 历史对话轮次（来自 CodeTurn 记录）
        file_hint: 用户期望修改的文件（可选，会追加到 prompt 中）
    """
    errors: list[str] = []
    warnings: list[str] = []

    key = settings.api.openai_compatible_api_key
    base = settings.api.openai_compatible_base_url
    model = settings.api.openai_compatible_model
    if not key or not base or not model:
        errors.append(
            "未配置 OpenAI 兼容 API：请在全局设置中填写接口地址、密钥与模型名称。"
        )
        return CodeCompileResponse(success=False, errors=errors)

    try:
        from openai import OpenAI
    except ImportError:
        errors.append("缺少依赖 openai：请执行 pip install openai")
        return CodeCompileResponse(success=False, errors=errors)

    file_context = _read_project_files(project_root)
    history_text = _turns_to_history_text(previous_turns or [])
    system_prompt = _build_system_prompt(file_context, history_text)

    user_content = prompt.strip()
    if file_hint:
        user_content = f"【目标文件】{file_hint}\n\n{user_content}"

    client = OpenAI(api_key=key, base_url=base.rstrip("/"))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    raw_text = ""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.15,
            response_format={"type": "json_object"},
        )
        raw_text = completion.choices[0].message.content or ""
    except Exception as exc:
        logger.exception("Code Studio compile API call failed")
        errors.append(f"API 调用失败：{exc}")
        return CodeCompileResponse(success=False, errors=errors)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Code Studio: failed to parse JSON response: %s", raw_text[:300])
        errors.append(f"AI 返回内容无法解析为 JSON：{exc}")
        return CodeCompileResponse(success=False, errors=errors)

    required = {"file_path", "new_content", "explanation"}
    missing = required - set(data.keys())
    if missing:
        errors.append(f"AI 返回 JSON 缺少必要字段：{missing}")
        return CodeCompileResponse(success=False, errors=errors)

    patch = CodeCompilePatch(
        file_path=str(data["file_path"]),
        new_content=str(data["new_content"]),
        explanation=str(data["explanation"]),
    )
    return CodeCompileResponse(success=True, patch=patch)

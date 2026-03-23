"""Natural language → StandardVideoJobRequest via OpenAI-compatible Chat API."""

from __future__ import annotations

import json
import logging
from typing import Any

from orchestrator.registry import ProjectRegistry

from shared.agent.catalog import build_agent_catalog
from shared.agent.schemas import AgentCompileResponse, StandardVideoJobRequest
from shared.agent.validate import validate_standard_request
from shared.config.settings import settings

logger = logging.getLogger(__name__)


def _system_prompt(catalog: dict[str, Any], schema_hint: str) -> str:
    return f"""你是「视频工程调度器」的编译器。你的唯一输出必须是**一个 JSON 对象**（不要 markdown，不要解释），
且必须能被解析为以下 TypeScript 接口（字段齐全）：

{schema_hint}

规则：
1. 根据用户的自然语言需求，从 catalog 中选择唯一的 project 与 task。
2. kwargs 必须是 JSON 对象，键名使用各任务 manifest 里 parameters 的 name；数值用 JSON 数字/布尔/字符串。
3. 视频平台常见映射：抖音/竖屏短视频 → platform 常用 \"douyin\"；B站横屏 → \"bilibili_landscape\" 等（以任务参数说明为准）。
4. 若用户需求模糊，选 default_task 并给出合理默认参数，并在 intent_summary 中写明假设。
5. 若用户是在「修改上一版」，请阅读 previous_json，合并变更后输出完整新 JSON（不要省略未改字段）。
6. 不要执行任何代码；只输出 JSON。

当前可用子项目与任务目录（catalog）：
{json.dumps(catalog, ensure_ascii=False, indent=2)}
"""


_SCHEMA_HINT = """
interface StandardVideoJobRequest {
  schema_version: "1.0";
  project: string;
  task: string;
  kwargs: Record<string, unknown>;
  intent_summary: string | null;
  revision_notes: string | null;
}
"""


def compile_natural_language(
    prompt: str,
    registry: ProjectRegistry,
    *,
    previous: StandardVideoJobRequest | None = None,
) -> AgentCompileResponse:
    """调用已配置的 OpenAI 兼容接口，将自然语言编译为标准模板。"""
    errors: list[str] = []
    warnings: list[str] = []

    key = settings.api.openai_compatible_api_key
    base = settings.api.openai_compatible_base_url
    model = settings.api.openai_compatible_model
    if not key or not base or not model:
        errors.append(
            "未配置 OpenAI 兼容 API：请在全局设置中填写接口地址、密钥与模型名称。"
        )
        return AgentCompileResponse(success=False, errors=errors, warnings=warnings)

    try:
        from openai import OpenAI
    except ImportError:
        errors.append("缺少依赖 openai：请执行 pip install openai")
        return AgentCompileResponse(success=False, errors=errors, warnings=warnings)

    catalog = build_agent_catalog(registry)
    client = OpenAI(api_key=key, base_url=base.rstrip("/"))
    user_content: str = prompt.strip()
    if previous is not None:
        user_content = (
            "【上一版标准模板 previous_json】\n"
            + previous.model_dump_json(indent=2)
            + "\n\n【本次修改需求】\n"
            + user_content
        )

    messages = [
        {"role": "system", "content": _system_prompt(catalog, _SCHEMA_HINT)},
        {"role": "user", "content": user_content},
    ]

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.exception("Agent compile API call failed")
        errors.append(f"模型调用失败: {exc}")
        return AgentCompileResponse(success=False, errors=errors, warnings=warnings)

    raw_text = (completion.choices[0].message.content or "").strip()
    if not raw_text:
        errors.append("模型返回空内容")
        return AgentCompileResponse(success=False, errors=errors, warnings=warnings)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        errors.append(f"模型返回非合法 JSON: {exc}")
        return AgentCompileResponse(
            success=False,
            errors=errors,
            warnings=warnings,
            raw_model_text=raw_text,
        )

    try:
        req = StandardVideoJobRequest.model_validate(data)
    except Exception as exc:
        errors.append(f"JSON 不符合 StandardVideoJobRequest: {exc}")
        return AgentCompileResponse(
            success=False,
            errors=errors,
            warnings=warnings,
            raw_model_text=raw_text,
        )

    v = validate_standard_request(req, registry)
    warnings.extend(v.warnings)
    if not v.valid:
        errors.extend(v.errors)
        return AgentCompileResponse(
            success=False,
            errors=errors,
            warnings=warnings,
            raw_model_text=raw_text,
        )

    # 获取任务的参数定义
    from shared.agent.catalog import _load_manifest_dict
    project = registry.get_project(req.project)
    task_parameters = None
    if project is not None:
        raw = _load_manifest_dict(project.manifest_path)
        tasks = raw.get("tasks", {})
        task_def = tasks.get(req.task, {})
        task_parameters = task_def.get("parameters")

    return AgentCompileResponse(
        success=True,
        standard_request=req,
        warnings=warnings,
        raw_model_text=raw_text,
        task_parameters=task_parameters,
    )

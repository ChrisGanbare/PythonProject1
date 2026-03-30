"""Agent-facing stable contracts for video jobs (versioned JSON)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class StandardVideoJobRequest(BaseModel):
    """统一模板：Agent / CLI / HTTP 提交给调度器的标准载荷。

    与控制台 ``POST /api/run/{project}/{task}`` 的 ``kwargs`` 语义一致，
    额外携带可审计的自然语言摘要与模式版本。
    """

    schema_version: Literal["1.0"] = Field(default="1.0", description="模板版本")
    project: str = Field(description="子项目 id，与 project_manifest 中 name 一致")
    task: str = Field(description="任务名，见各子项目 manifest tasks")
    kwargs: dict[str, Any] = Field(default_factory=dict, description="传给入口可调用对象的参数")
    intent_summary: str | None = Field(
        default=None,
        description="用户原始意图的一句话摘要，便于日志与复现",
    )
    revision_notes: str | None = Field(
        default=None,
        description="相对上一版模板的修改说明（若有迭代）",
    )

    model_config = {"extra": "forbid"}


class AgentCompileRequest(BaseModel):
    """HTTP：自然语言 → 标准模板。"""

    prompt: str = Field(min_length=1, description="视频制作需求（自然语言）")
    previous: StandardVideoJobRequest | None = Field(
        default=None,
        description="上一轮标准模板；若提供则视为在上一版上修改需求",
    )
    session_id: str | None = Field(
        default=None,
        description="意图会话 id；若提供且 persist_turns=True，则写入数据库供多轮追溯",
    )
    persist_turns: bool = Field(
        default=True,
        description="在 session_id 下持久化本轮用户语句与编译结果",
    )


class AgentCompileResponse(BaseModel):
    """编译结果。"""

    success: bool
    standard_request: StandardVideoJobRequest | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_model_text: str | None = Field(default=None, description="模型原始 JSON 文本，仅调试")
    task_parameters: list[dict[str, Any]] | None = Field(
        default=None,
        description="Task 的参数定义（从 manifest 中提取），便于前端显示"
    )


class AgentValidateResponse(BaseModel):
    """校验标准模板是否可被当前注册表执行。"""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

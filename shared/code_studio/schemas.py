"""Code Studio：Pydantic 数据契约。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 请求 / 响应
# ---------------------------------------------------------------------------


class CodeCompileRequest(BaseModel):
    """HTTP 请求体：将自然语言代码需求编译为文件补丁。"""

    prompt: str = Field(min_length=1, description="对代码的自然语言描述需求")
    file_hint: str | None = Field(
        default=None,
        description="用户期望修改的目标文件路径（相对 project_root），可为空让 AI 自动选择",
    )


class CodeCompilePatch(BaseModel):
    """AI 返回的单文件补丁内容。"""

    file_path: str = Field(description="受影响文件路径（相对 project_root），如 renderer/viz_backend.py")
    new_content: str = Field(description="文件完整新内容（替换写入，非 diff）")
    explanation: str = Field(description="本次变更的简要说明（中文，≤120字）")


class CodeCompileResponse(BaseModel):
    """编译结果。"""

    success: bool
    patch: CodeCompilePatch | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ApplyPatchRequest(BaseModel):
    """HTTP 请求体：将补丁写入磁盘。"""

    turn_id: int = Field(description="要应用的 CodeTurn id")
    confirm: bool = Field(default=True, description="安全开关：必须为 true 才会实际写入")


class ApplyPatchResponse(BaseModel):
    """写入结果。"""

    success: bool
    written_path: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# 用于 HTTP 响应的投影（不含 SQLAlchemy 关联对象）
# ---------------------------------------------------------------------------


class CodeTurnOut(BaseModel):
    """单轮的 HTTP 投影。"""

    id: int
    seq: int
    role: str
    content_text: str | None
    code_patch: str | None
    file_path: str | None
    applied_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CodeSessionOut(BaseModel):
    """会话（含所有轮次）的 HTTP 投影。"""

    id: str
    project_name: str
    task_name: str | None
    title: str | None
    created_at: datetime
    updated_at: datetime
    turns: list[CodeTurnOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CreateCodeSessionRequest(BaseModel):
    """创建会话请求体。"""

    project_name: str = Field(min_length=1)
    task_name: str | None = None
    title: str | None = None

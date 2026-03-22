"""控制面 ORM：渲染任务、意图会话（自然语言迭代）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.studio.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntentSession(Base):
    """一条「视频需求」对话线程：可挂多轮用户描述与编译结果。"""

    __tablename__ = "intent_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # 客户端标签、来源等

    turns: Mapped[list["IntentTurn"]] = relationship(
        back_populates="session",
        order_by="IntentTurn.seq",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list["RenderJob"]] = relationship(back_populates="intent_session")


class IntentTurn(Base):
    """会话内一轮：用户自然语言或系统编译结果。"""

    __tablename__ = "intent_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("intent_sessions.id", ondelete="CASCADE"))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user | assistant | system
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    compiled_template_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_compile_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    linked_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["IntentSession"] = relationship(back_populates="turns")


class RenderJob(Base):
    """异步渲染任务：与控制台 / Agent 共用同一持久化模型。"""

    __tablename__ = "render_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    project: Mapped[str] = mapped_column(String(256), nullable=False)
    task: Mapped[str] = mapped_column(String(256), nullable=False)
    kwargs_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    intent_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("intent_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    intent_session: Mapped["IntentSession | None"] = relationship(back_populates="jobs")

    def log_list(self) -> list[str]:
        import json

        try:
            data = json.loads(self.log_json or "[]")
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def set_log_list(self, items: list[str]) -> None:
        import json

        self.log_json = json.dumps(items, ensure_ascii=False)

    def append_log(self, line: str) -> None:
        lst = self.log_list()
        lst.append(line)
        self.set_log_list(lst)


# ---------------------------------------------------------------------------
# Code Studio：代码工坊会话与对话轮次
# ---------------------------------------------------------------------------


class CodeSession(Base):
    """代码工坊会话：聚焦某个子项目的代码迭代对话线程。"""

    __tablename__ = "code_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    task_name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    turns: Mapped[list["CodeTurn"]] = relationship(
        back_populates="session",
        order_by="CodeTurn.seq",
        cascade="all, delete-orphan",
    )


class CodeTurn(Base):
    """代码工坊对话轮次：用户需求或 AI 返回的代码补丁。"""

    __tablename__ = "code_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("code_sessions.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user | assistant
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 完整新文件内容（非 diff，方便直接写回磁盘）
    code_patch: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 受影响的文件路径（相对 project_root，如 renderer/viz_backend.py）
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["CodeSession"] = relationship(back_populates="turns")

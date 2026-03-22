"""Code Studio：CodeSession / CodeTurn CRUD + 文件写入 facade。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from shared.studio.db.base import SessionLocal, get_engine
from shared.studio.db.models import CodeSession, CodeTurn


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


def create_code_session(
    *,
    project_name: str,
    task_name: str | None = None,
    title: str | None = None,
) -> str:
    """创建新会话，返回会话 uuid。若未提供 title 则自动生成序号标题。"""
    with SessionLocal(bind=get_engine()) as db:
        if not title:
            # 统计同 project+task 下已有会话数，生成序号如「render 迭代 #2」
            count_q = select(func.count()).select_from(CodeSession).where(
                CodeSession.project_name == project_name
            )
            if task_name:
                count_q = count_q.where(CodeSession.task_name == task_name)
            count = db.execute(count_q).scalar() or 0
            base_label = task_name or project_name
            title = f"{base_label} 迭代 #{count + 1}"
        s = CodeSession(project_name=project_name, task_name=task_name, title=title)
        db.add(s)
        db.commit()
        return s.id


def get_code_session_detail(session_id: str) -> dict[str, Any] | None:
    """返回会话及所有轮次，未找到返回 None。"""
    with SessionLocal(bind=get_engine()) as db:
        s = db.get(CodeSession, session_id)
        if s is None:
            return None
        turns = (
            db.execute(
                select(CodeTurn)
                .where(CodeTurn.session_id == session_id)
                .order_by(CodeTurn.seq)
            )
            .scalars()
            .all()
        )
    return {
        "id": s.id,
        "project_name": s.project_name,
        "task_name": s.task_name,
        "title": s.title,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "turns": [_turn_to_dict(t) for t in turns],
    }


def list_code_sessions(
    *,
    project_name: str | None = None,
    task_name: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    """列举会话列表，可按 project_name / task_name 过滤。"""
    limit = max(1, min(limit, 100))
    with SessionLocal(bind=get_engine()) as db:
        q = select(CodeSession).order_by(CodeSession.updated_at.desc()).limit(limit)
        if project_name:
            q = q.where(CodeSession.project_name == project_name)
        if task_name:
            q = q.where(CodeSession.task_name == task_name)
        rows = db.execute(q).scalars().all()
    return {
        "items": [
            {
                "id": r.id,
                "project_name": r.project_name,
                "task_name": r.task_name,
                "title": r.title,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    }


def delete_code_session(session_id: str) -> bool:
    """删除会话及其所有轮次（CASCADE）。不存在返回 False。"""
    with SessionLocal(bind=get_engine()) as db:
        s = db.get(CodeSession, session_id)
        if s is None:
            return False
        db.delete(s)
        db.commit()
    return True


# ---------------------------------------------------------------------------
# Turn CRUD
# ---------------------------------------------------------------------------


def append_user_turn(session_id: str, prompt: str) -> int:
    """追加用户轮次，返回新轮次 id。"""
    with SessionLocal(bind=get_engine()) as db:
        if db.get(CodeSession, session_id) is None:
            raise ValueError(f"code_session not found: {session_id}")
        seq = _next_seq(db, session_id)
        turn = CodeTurn(session_id=session_id, seq=seq, role="user", content_text=prompt)
        db.add(turn)
        db.commit()
        return turn.id


def append_assistant_turn(
    session_id: str,
    *,
    explanation: str,
    file_path: str,
    code_patch: str,
) -> int:
    """追加 AI 助手轮次，返回新轮次 id。"""
    with SessionLocal(bind=get_engine()) as db:
        if db.get(CodeSession, session_id) is None:
            raise ValueError(f"code_session not found: {session_id}")
        seq = _next_seq(db, session_id)
        turn = CodeTurn(
            session_id=session_id,
            seq=seq,
            role="assistant",
            content_text=explanation,
            file_path=file_path,
            code_patch=code_patch,
        )
        db.add(turn)
        db.commit()
        return turn.id


def get_turn_by_id(turn_id: int) -> dict[str, Any] | None:
    """按 id 获取单个轮次。"""
    with SessionLocal(bind=get_engine()) as db:
        t = db.get(CodeTurn, turn_id)
        if t is None:
            return None
        return _turn_to_dict(t)


# ---------------------------------------------------------------------------
# 文件写入
# ---------------------------------------------------------------------------


def apply_patch(turn_id: int, project_root: Path) -> tuple[bool, str]:
    """将指定轮次的 code_patch 写入磁盘，返回 (success, message)。

    使用原子替换（write temp → os.replace）避免写入中断导致文件损坏。
    """
    import os
    import tempfile

    with SessionLocal(bind=get_engine()) as db:
        turn = db.get(CodeTurn, turn_id)
        if turn is None:
            return False, f"turn not found: {turn_id}"
        if turn.role != "assistant":
            return False, "只有 assistant 轮次才能应用补丁"
        if not turn.code_patch:
            return False, "该轮次没有可应用的代码补丁"
        if not turn.file_path:
            return False, "该轮次没有指定目标文件"

        file_path_str: str = turn.file_path
        code_patch: str = turn.code_patch
        session_id: str = turn.session_id

    target = (project_root / file_path_str).resolve()

    # 安全检查：目标文件必须在 project_root 内
    try:
        target.relative_to(project_root.resolve())
    except ValueError:
        return False, f"目标路径逃逸 project_root：{file_path_str}"

    target.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=target.parent, prefix=".cs_patch_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(code_patch)
        os.replace(tmp_path, target)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False, f"文件写入失败：{exc}"

    # 记录写入时间
    with SessionLocal(bind=get_engine()) as db:
        t = db.get(CodeTurn, turn_id)
        if t is not None:
            t.applied_at = datetime.now(timezone.utc)
            # 触发 session updated_at 更新
            s = db.get(CodeSession, session_id)
            if s:
                s.updated_at = datetime.now(timezone.utc)
            db.commit()

    return True, str(target)


# ---------------------------------------------------------------------------
# 为 compiler 提供历史对话（最近 N 轮，仅含文本，不含完整代码）
# ---------------------------------------------------------------------------


def get_recent_turns_for_context(session_id: str, *, n: int = 10) -> list[dict[str, Any]]:
    """返回最近 n 轮的对话摘要（content_text + file_path），供 compiler 注入 history。"""
    with SessionLocal(bind=get_engine()) as db:
        turns = (
            db.execute(
                select(CodeTurn)
                .where(CodeTurn.session_id == session_id)
                .order_by(CodeTurn.seq.desc())
                .limit(n)
            )
            .scalars()
            .all()
        )
    return [
        {"role": t.role, "content_text": t.content_text, "file_path": t.file_path}
        for t in reversed(turns)
    ]


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _next_seq(db, session_id: str) -> int:
    val = db.scalar(
        select(func.coalesce(func.max(CodeTurn.seq), 0)).where(CodeTurn.session_id == session_id)
    )
    return int(val or 0) + 1


def _turn_to_dict(t: CodeTurn) -> dict[str, Any]:
    return {
        "id": t.id,
        "seq": t.seq,
        "role": t.role,
        "content_text": t.content_text,
        "code_patch": t.code_patch,
        "file_path": t.file_path,
        "applied_at": t.applied_at.isoformat() if t.applied_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

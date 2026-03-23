"""意图会话：自然语言多轮与编译结果链。"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select

from shared.studio.db.base import SessionLocal, get_engine
from shared.studio.db.models import IntentSession, IntentTurn


def create_intent_session(*, title: str | None = None, meta: dict[str, Any] | None = None) -> str:
    with SessionLocal(bind=get_engine()) as session:
        s = IntentSession(
            title=title,
            meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        session.add(s)
        session.commit()
        return s.id


def _next_seq(session_id: str) -> int:
    with SessionLocal(bind=get_engine()) as session:
        m = session.scalar(select(func.coalesce(func.max(IntentTurn.seq), 0)).where(IntentTurn.session_id == session_id))
        return int(m or 0) + 1


def append_user_turn(session_id: str, content: str) -> int:
    with SessionLocal(bind=get_engine()) as session:
        if session.get(IntentSession, session_id) is None:
            raise ValueError(f"session not found: {session_id}")
        seq = session.scalar(
            select(func.coalesce(func.max(IntentTurn.seq), 0)).where(IntentTurn.session_id == session_id)
        )
        seq = int(seq or 0) + 1
        turn = IntentTurn(session_id=session_id, seq=seq, role="user", content_text=content)
        session.add(turn)
        session.commit()
        return turn.id


def append_compile_turn(
    session_id: str,
    *,
    prompt_snapshot: str,
    compile_response_json: str,
    standard_template_json: str | None,
) -> int:
    with SessionLocal(bind=get_engine()) as session:
        if session.get(IntentSession, session_id) is None:
            raise ValueError(f"session not found: {session_id}")
        seq = session.scalar(
            select(func.coalesce(func.max(IntentTurn.seq), 0)).where(IntentTurn.session_id == session_id)
        )
        seq = int(seq or 0) + 1
        turn = IntentTurn(
            session_id=session_id,
            seq=seq,
            role="assistant",
            content_text=prompt_snapshot,
            compiled_template_json=standard_template_json,
            raw_compile_response_json=compile_response_json,
        )
        session.add(turn)
        session.commit()
        return turn.id


def get_intent_session_detail(session_id: str) -> dict[str, Any] | None:
    with SessionLocal(bind=get_engine()) as session:
        s = session.get(IntentSession, session_id)
        if s is None:
            return None
        turns = (
            session.execute(
                select(IntentTurn).where(IntentTurn.session_id == session_id).order_by(IntentTurn.seq)
            )
            .scalars()
            .all()
        )
        return {
            "id": s.id,
            "title": s.title,
            "is_completed": s.is_completed,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "meta": json.loads(s.meta_json) if s.meta_json else None,
            "turns": [
                {
                    "id": t.id,
                    "seq": t.seq,
                    "role": t.role,
                    "content_text": t.content_text,
                    "compiled_template": json.loads(t.compiled_template_json)
                    if t.compiled_template_json
                    else None,
                    "linked_job_id": t.linked_job_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in turns
            ],
        }


def list_intent_sessions(*, limit: int = 30) -> dict[str, Any]:
    limit = max(1, min(limit, 100))
    with SessionLocal(bind=get_engine()) as session:
        rows = (
            session.execute(select(IntentSession).order_by(IntentSession.updated_at.desc()).limit(limit))
            .scalars()
            .all()
        )
    return {
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "is_completed": r.is_completed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    }


def update_intent_session_title(session_id: str, title: str | None) -> bool:
    """修改会话标题。返回是否成功。"""
    with SessionLocal(bind=get_engine()) as session:
        s = session.get(IntentSession, session_id)
        if s is None:
            return False
        s.title = title
        session.commit()
        return True


def delete_intent_session(session_id: str) -> bool:
    """删除会话及其所有turns。仅允许已完成的会话被删除。返回是否成功。"""
    with SessionLocal(bind=get_engine()) as session:
        s = session.get(IntentSession, session_id)
        if s is None:
            return False
        # 防止删除进行中的会话（未完成的会话）
        if not s.is_completed:
            return False
        session.delete(s)
        session.commit()
        return True


def mark_intent_session_completed(session_id: str) -> bool:
    """标记会话为已完成。返回是否成功。"""
    with SessionLocal(bind=get_engine()) as session:
        s = session.get(IntentSession, session_id)
        if s is None:
            return False
        s.is_completed = True
        session.commit()
        return True

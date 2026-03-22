"""SQLite-backed screenplay script versioning (draft / approved)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from shared.content.screenplay import Screenplay
from shared.utils.time import utc_now


class ScriptVersionStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"


@dataclass(frozen=True)
class ScreenplayVersionRecord:
    script_id: str
    version: int
    parent_version: int | None
    status: ScriptVersionStatus
    screenplay: Screenplay
    created_at: datetime
    goal: str
    platform: str
    topic: str


class ScreenplayStore:
    """Versioned storage for `Screenplay` documents."""

    def __init__(self, db_path: Path | None = None) -> None:
        from shared.config.settings import settings

        base = db_path or (settings.library_dir / "screenplays.db")
        self.db_path = Path(base)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS screenplay_scripts (
                    script_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL DEFAULT '',
                    platform TEXT NOT NULL DEFAULT '',
                    topic TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS screenplay_versions (
                    script_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    parent_version INTEGER,
                    status TEXT NOT NULL,
                    screenplay_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (script_id, version),
                    FOREIGN KEY (script_id) REFERENCES screenplay_scripts(script_id)
                );

                CREATE INDEX IF NOT EXISTS idx_versions_script
                ON screenplay_versions(script_id, version DESC);
                """
            )

    def create_script(self, *, goal: str = "", platform: str = "", topic: str = "") -> str:
        script_id = str(uuid.uuid4())
        now = utc_now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO screenplay_scripts (script_id, goal, platform, topic, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (script_id, goal, platform, topic, now, now),
            )
        return script_id

    def _touch_script(self, conn: sqlite3.Connection, script_id: str) -> None:
        conn.execute(
            "UPDATE screenplay_scripts SET updated_at = ? WHERE script_id = ?",
            (utc_now().isoformat(), script_id),
        )

    def add_version(
        self,
        script_id: str,
        screenplay: Screenplay,
        *,
        status: ScriptVersionStatus = ScriptVersionStatus.DRAFT,
        parent_version: int | None = None,
    ) -> int:
        payload = screenplay.model_dump(mode="json")
        screenplay_json = json.dumps(payload, ensure_ascii=False)
        now = utc_now().isoformat()
        with self._connect() as conn:
            exists = conn.execute(
                "SELECT 1 FROM screenplay_scripts WHERE script_id = ?",
                (script_id,),
            ).fetchone()
            if not exists:
                raise ValueError(f"unknown script_id: {script_id}")
            row = conn.execute(
                "SELECT MAX(version) FROM screenplay_versions WHERE script_id = ?",
                (script_id,),
            ).fetchone()
            next_version = (int(row[0] or 0) + 1)
            conn.execute(
                """
                INSERT INTO screenplay_versions
                (script_id, version, parent_version, status, screenplay_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (script_id, next_version, parent_version, status.value, screenplay_json, now),
            )
            self._touch_script(conn, script_id)
        return next_version

    def set_version_status(self, script_id: str, version: int, status: ScriptVersionStatus) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE screenplay_versions SET status = ?
                WHERE script_id = ? AND version = ?
                """,
                (status.value, script_id, version),
            )
            if cur.rowcount == 0:
                raise ValueError(f"version not found: {script_id}@{version}")
            self._touch_script(conn, script_id)

    def get_version(self, script_id: str, version: int | None = None) -> ScreenplayVersionRecord | None:
        with self._connect() as conn:
            if version is None:
                row = conn.execute(
                    """
                    SELECT v.script_id, v.version, v.parent_version, v.status, v.screenplay_json, v.created_at,
                           s.goal, s.platform, s.topic
                    FROM screenplay_versions v
                    JOIN screenplay_scripts s ON s.script_id = v.script_id
                    WHERE v.script_id = ?
                    ORDER BY v.version DESC
                    LIMIT 1
                    """,
                    (script_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT v.script_id, v.version, v.parent_version, v.status, v.screenplay_json, v.created_at,
                           s.goal, s.platform, s.topic
                    FROM screenplay_versions v
                    JOIN screenplay_scripts s ON s.script_id = v.script_id
                    WHERE v.script_id = ? AND v.version = ?
                    """,
                    (script_id, version),
                ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def list_scripts(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.script_id, s.goal, s.platform, s.topic, s.created_at, s.updated_at,
                       MAX(v.version) AS latest_version,
                       SUM(CASE WHEN v.status = 'approved' THEN 1 ELSE 0 END) AS approved_count
                FROM screenplay_scripts s
                LEFT JOIN screenplay_versions v ON v.script_id = s.script_id
                GROUP BY s.script_id
                ORDER BY s.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_versions(self, script_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT version, parent_version, status, created_at
                FROM screenplay_versions
                WHERE script_id = ?
                ORDER BY version ASC
                """,
                (script_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> ScreenplayVersionRecord:
        data = json.loads(row["screenplay_json"])
        return ScreenplayVersionRecord(
            script_id=row["script_id"],
            version=int(row["version"]),
            parent_version=int(row["parent_version"]) if row["parent_version"] is not None else None,
            status=ScriptVersionStatus(row["status"]),
            screenplay=Screenplay.model_validate(data),
            created_at=datetime.fromisoformat(row["created_at"]),
            goal=row["goal"] or "",
            platform=row["platform"] or "",
            topic=row["topic"] or "",
        )

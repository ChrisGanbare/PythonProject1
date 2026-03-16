"""Task lifecycle management."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable

from shared.config.settings import settings


class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    task_id: str
    status: TaskStatus
    progress: int = 0
    current_step: str = ""
    eta_seconds: int | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return data


class TaskManager:
    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or settings.cache_dir / "tasks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, TaskInfo] = {}
        self._callbacks: dict[str, Callable[[TaskInfo], None]] = {}
        self._load_tasks()

    def _load_tasks(self) -> None:
        for file in self.storage_dir.glob("*.json"):
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
                task = TaskInfo(
                    task_id=payload["task_id"],
                    status=TaskStatus(payload.get("status", TaskStatus.QUEUED.value)),
                    progress=payload.get("progress", 0),
                    current_step=payload.get("current_step", ""),
                    eta_seconds=payload.get("eta_seconds"),
                    error_message=payload.get("error_message"),
                    created_at=datetime.fromisoformat(payload["created_at"]),
                    updated_at=datetime.fromisoformat(payload["updated_at"]),
                    completed_at=datetime.fromisoformat(payload["completed_at"])
                    if payload.get("completed_at")
                    else None,
                )
                self._tasks[task.task_id] = task
            except Exception:
                continue

    def _persist_task(self, task: TaskInfo) -> None:
        path = self.storage_dir / f"{task.task_id}.json"
        path.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def create_task(self, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        task = TaskInfo(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            progress=kwargs.get("progress", 0),
            current_step=kwargs.get("current_step", "queued"),
            eta_seconds=kwargs.get("eta_seconds"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._tasks[task_id] = task
        self._persist_task(task)
        return task_id

    def get_task(self, task_id: str) -> TaskInfo | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[TaskInfo]:
        items = list(self._tasks.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        return sorted(items, key=lambda task: task.created_at, reverse=True)

    def update_task(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        progress: int | None = None,
        current_step: str | None = None,
        eta_seconds: int | None = None,
        error_message: str | None = None,
    ) -> TaskInfo | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None

        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = max(0, min(100, progress))
        if current_step is not None:
            task.current_step = current_step
        if eta_seconds is not None:
            task.eta_seconds = eta_seconds
        if error_message is not None:
            task.error_message = error_message

        task.updated_at = datetime.utcnow()

        if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            task.completed_at = datetime.utcnow()

        self._persist_task(task)

        callback = self._callbacks.get(task_id)
        if callback:
            callback(task)

        return task

    def register_callback(self, task_id: str, callback: Callable[[TaskInfo], None]) -> None:
        self._callbacks[task_id] = callback

    def cleanup_old_tasks(self, max_age_hours: int = 168) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed = 0

        for task_id, task in list(self._tasks.items()):
            if task.completed_at and task.completed_at < cutoff:
                path = self.storage_dir / f"{task_id}.json"
                if path.exists():
                    path.unlink()
                del self._tasks[task_id]
                removed += 1

        return removed


class ProgressTracker:
    def __init__(self, task_manager: TaskManager, task_id: str, total_steps: int = 100):
        self.task_manager = task_manager
        self.task_id = task_id
        self.total_steps = max(1, total_steps)
        self.current_step = 0

    def start_step(self, step_name: str) -> None:
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.PROCESSING,
            current_step=step_name,
        )

    def update(self, step: int | None = None, step_name: str | None = None) -> None:
        if step is not None:
            self.current_step = step
        progress = int((self.current_step / self.total_steps) * 100)
        self.task_manager.update_task(
            self.task_id,
            progress=progress,
            current_step=step_name or f"step {self.current_step}/{self.total_steps}",
        )

    def complete(self) -> None:
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            current_step="completed",
        )

    def fail(self, error_message: str) -> None:
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.FAILED,
            current_step="failed",
            error_message=error_message,
        )

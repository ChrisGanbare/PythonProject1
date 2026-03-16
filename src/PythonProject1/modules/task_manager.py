"""
任务管理模块
后台任务队列、状态跟踪等（支持 APScheduler）
"""

import logging
import uuid
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import asyncio

from config.settings import settings
from models.exceptions import VideoProjectException
from models.schemas import TaskStatus


logger = logging.getLogger(__name__)


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    status: TaskStatus
    progress: int = 0
    current_step: str = ""
    eta_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class TaskManager:
    """任务管理器"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """初始化任务管理器
        
        Args:
            storage_dir: 任务状态存储目录
        """
        self.storage_dir = storage_dir or settings.cache_dir / "tasks"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._tasks: Dict[str, TaskInfo] = {}
        self._task_callbacks: Dict[str, Callable] = {}
        
        self._load_tasks()
        logger.info(f"[TaskManager] 初始化完成 | 存储目录: {self.storage_dir}")
    
    def _load_tasks(self) -> None:
        """从存储加载任务"""
        try:
            for task_file in self.storage_dir.glob("*.json"):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        task_id = data.get("task_id")
                        if task_id:
                            status = TaskStatus(data.get("status", TaskStatus.QUEUED.value))
                            task = TaskInfo(
                                task_id=task_id,
                                status=status,
                                progress=data.get("progress", 0),
                                current_step=data.get("current_step", ""),
                                created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
                            )
                            self._tasks[task_id] = task
                except Exception as e:
                    logger.warning(f"[TaskManager] 加载任务失败: {task_file} - {e}")
        except Exception as e:
            logger.warning(f"[TaskManager] 加载任务异常: {e}")
    
    def create_task(self, **kwargs) -> str:
        """创建新任务
        
        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            **{k: v for k, v in kwargs.items() if k in ['progress', 'current_step', 'eta_seconds']}
        )
        
        self._tasks[task_id] = task
        self._save_task(task)
        
        logger.info(f"[TaskManager] 创建任务: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self._tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        eta_seconds: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TaskInfo]:
        """更新任务状态
        
        Returns:
            更新后的任务对象
        """
        task = self._tasks.get(task_id)
        if not task:
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
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.utcnow()
        
        self._save_task(task)
        
        # 触发回调
        if task_id in self._task_callbacks:
            try:
                self._task_callbacks[task_id](task)
            except Exception as e:
                logger.warning(f"[TaskManager] 回调执行失败: {e}")
        
        return task
    
    def _save_task(self, task: TaskInfo) -> None:
        """保存任务状态"""
        try:
            task_file = self.storage_dir / f"{task.task_id}.json"
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[TaskManager] 保存任务失败: {task.task_id} - {e}")
    
    def register_callback(self, task_id: str, callback: Callable[[TaskInfo], None]) -> None:
        """注册任务状态变化回调"""
        self._task_callbacks[task_id] = callback
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> list:
        """列出任务
        
        Args:
            status: 过滤状态（若为空返回所有）
        
        Returns:
            任务列表
        """
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    def cleanup_old_tasks(self, max_age_hours: int = 168) -> int:
        """清理过期任务
        
        Args:
            max_age_hours: 最大保留时长（小时）
        
        Returns:
            清理的任务数
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        removed_count = 0
        
        for task_id, task in list(self._tasks.items()):
            if task.completed_at and task.completed_at < cutoff_time:
                try:
                    task_file = self.storage_dir / f"{task_id}.json"
                    if task_file.exists():
                        task_file.unlink()
                    del self._tasks[task_id]
                    removed_count += 1
                    logger.debug(f"[TaskManager] 删除过期任务: {task_id}")
                except Exception as e:
                    logger.warning(f"[TaskManager] 删除任务失败: {e}")
        
        if removed_count > 0:
            logger.info(f"[TaskManager] 清理 {removed_count} 个过期任务")
        
        return removed_count


class ProgressTracker:
    """进度追踪器"""
    
    def __init__(self, task_manager: TaskManager, task_id: str, total_steps: int = 100):
        """初始化进度追踪器
        
        Args:
            task_manager: 任务管理器
            task_id: 任务 ID
            total_steps: 总步数
        """
        self.task_manager = task_manager
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
    
    def start_step(self, step_name: str) -> None:
        """开始新的步骤"""
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.PROCESSING,
            current_step=step_name,
        )
        logger.debug(f"[进度] 开始步骤: {step_name}")
    
    def update(self, step: int = None, step_name: str = None) -> None:
        """更新进度
        
        Args:
            step: 当前步骤号
            step_name: 步骤名称
        """
        if step is not None:
            self.current_step = step
        
        progress = int((self.current_step / self.total_steps) * 100)
        
        self.task_manager.update_task(
            self.task_id,
            progress=progress,
            current_step=step_name or f"Step {self.current_step}/{self.total_steps}",
        )
    
    def complete(self) -> None:
        """标记任务完成"""
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            current_step="Completed",
        )
        logger.info(f"[进度] 任务完成: {self.task_id}")
    
    def fail(self, error_message: str) -> None:
        """标记任务失败"""
        self.task_manager.update_task(
            self.task_id,
            status=TaskStatus.FAILED,
            error_message=error_message,
            current_step="Failed",
        )
        logger.error(f"[进度] 任务失败: {self.task_id} - {error_message}")


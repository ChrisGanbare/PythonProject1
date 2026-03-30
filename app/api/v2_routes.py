"""
快速图表视频 API（/api/video/v2）

作业与 Studio 共用持久化：project=v2_templates, task=render。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from orchestrator.registry import ProjectRegistry

from shared.ops.studio.services.job_lifecycle import (
    get_job_public_dict,
    run_render_job_task,
    schedule_render_job,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video/v2", tags=["quick video v2"])

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # app/api/ → app/ → root
_REGISTRY = ProjectRegistry(_REPO_ROOT)


def _repo_root() -> Path:
    return _REPO_ROOT


def _registry() -> ProjectRegistry:
    _REGISTRY.discover()
    return _REGISTRY


# ========== 数据模型 ==========


class VideoTemplateChoice(BaseModel):
    """模板选择"""

    template_id: str = Field(..., description="模板 ID")
    template_name: str


class VideoDataInput(BaseModel):
    """数据输入"""

    input_mode: str = Field("manual", description="输入方式：manual/upload")
    labels: str = Field("", description="标签/日期 (逗号分隔)")
    values: str = Field("", description="数值 (逗号分隔)")
    series_name: str = Field("", description="系列名称")
    file_path: Optional[str] = Field(None, description="上传文件路径")


class VideoBrandChoice(BaseModel):
    """品牌选择"""

    brand_id: str = Field("default", description="品牌 ID")


class VideoCreateRequest(BaseModel):
    """视频创建请求"""

    template: VideoTemplateChoice
    data: VideoDataInput
    brand: VideoBrandChoice
    platform: str = Field("bilibili", description="目标平台")


class VideoCreateResponse(BaseModel):
    """视频创建响应"""

    job_id: str
    status: str
    message: str
    output_path: Optional[str] = None
    created_at: datetime


class VideoJobStatus(BaseModel):
    """作业状态（与旧版向导兼容的字段名）"""

    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ========== 解析与映射 ==========


def _parse_chart_payload(request: VideoCreateRequest) -> dict[str, Any]:
    """将向导请求解析为 v2_templates.run_render 的 data 字段。"""
    data_input = request.data
    labels_raw = data_input.labels
    values_raw = data_input.values

    if isinstance(labels_raw, str):
        labels_normalized = labels_raw.replace("，", ",").strip()
        labels = [l.strip() for l in labels_normalized.split(",") if l.strip()]
    elif isinstance(labels_raw, list):
        labels = [str(l).strip() for l in labels_raw if str(l).strip()]
    else:
        raise ValueError(f"labels 格式错误：期望字符串或数组，得到 {type(labels_raw)}")

    if isinstance(values_raw, str):
        values_normalized = values_raw.replace("，", ",").strip()
        values = [float(v.strip()) for v in values_normalized.split(",") if v.strip()]
    elif isinstance(values_raw, list):
        values = [float(v) for v in values_raw if v is not None and str(v).strip()]
    else:
        raise ValueError(f"values 格式错误：期望字符串或数组，得到 {type(values_raw)}")

    if len(labels) != len(values):
        raise ValueError(f"标签和数值数量不匹配：labels={len(labels)}, values={len(values)}")

    return {
        "date": labels,
        "category": [data_input.series_name or "Series"] * len(labels),
        "value": values,
    }


def _extract_video_path(result: dict[str, Any] | None) -> str | None:
    if not isinstance(result, dict):
        return None
    p = result.get("final_video_path") or result.get("output_path")
    if p is None:
        return None
    return str(p)


def _parse_iso_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _map_to_video_job_status(job_id: str, pub: dict[str, Any]) -> VideoJobStatus:
    """将 Studio 作业字典映射为向导使用的状态形状。"""
    raw = pub.get("status") or "pending"
    messages = {
        "pending": ("pending", 0, "等待执行..."),
        "running": ("processing", 50, "渲染中..."),
        "success": ("completed", 100, "视频生成成功"),
        "failed": ("failed", 0, pub.get("error") or "渲染失败"),
    }
    vstatus, progress, base_msg = messages.get(
        raw, ("pending", 0, "未知状态")
    )
    if raw == "failed" and pub.get("error"):
        msg = f"生成失败：{pub['error']}"
    elif raw == "success":
        msg = base_msg
    else:
        msg = base_msg

    result = pub.get("result")
    out_path = _extract_video_path(result if isinstance(result, dict) else None)

    created = _parse_iso_dt(pub.get("created_at")) or datetime.now(timezone.utc)
    completed = _parse_iso_dt(pub.get("finished_at"))

    err = None
    if raw == "failed":
        err = pub.get("error")

    return VideoJobStatus(
        job_id=job_id,
        status=vstatus,
        progress=progress,
        message=msg,
        output_path=out_path,
        error=err,
        created_at=created,
        completed_at=completed,
    )


# ========== API 端点 ==========


@router.post("/create", response_model=VideoCreateResponse)
async def create_video(request: VideoCreateRequest, background_tasks: BackgroundTasks):
    """
    创建视频：持久化 RenderJob 并后台执行 v2_templates.render。
    """
    reg = _registry()
    project = reg.get_project("v2_templates")
    if project is None:
        raise HTTPException(status_code=500, detail="未注册 v2_templates 项目")

    try:
        chart_data = _parse_chart_payload(request)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    template_id = request.template.template_id
    brand_id = request.brand.brand_id
    platform = request.platform or "bilibili"

    kwargs: dict[str, Any] = {
        "template": template_id,
        "data": chart_data,
        "brand": brand_id,
        "platform": platform,
    }

    job_id = schedule_render_job(
        project="v2_templates",
        task="render",
        kwargs=kwargs,
        intent_summary=None,
        template_snapshot=None,
        session_id=None,
    )

    # job_id 确定后，注入绝对输出路径（runtime/outputs/{job_id}.mp4）
    output_dir = _repo_root() / "runtime" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"{job_id}.mp4")
    kwargs_with_path = {**kwargs, "output_path": output_path}

    background_tasks.add_task(
        run_render_job_task,
        job_id,
        project,
        "render",
        kwargs_with_path,
    )

    now = datetime.now(timezone.utc)
    return VideoCreateResponse(
        job_id=job_id,
        status="pending",
        message="视频任务已提交，正在后台渲染",
        created_at=now,
    )


@router.get("/status/{job_id}", response_model=VideoJobStatus)
async def get_job_status(job_id: str):
    pub = get_job_public_dict(job_id)
    if pub is None:
        raise HTTPException(status_code=404, detail="作业不存在")
    return _map_to_video_job_status(job_id, pub)


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """下载生成的视频（成功任务，路径来自 result）。"""
    from fastapi.responses import FileResponse

    pub = get_job_public_dict(job_id)
    if pub is None:
        raise HTTPException(status_code=404, detail="作业不存在")

    if pub.get("status") not in ("success", "completed"):
        detail = f"作业状态为 {pub.get('status')}，尚未完成或已失败"
        raise HTTPException(status_code=400, detail=detail)

    result = pub.get("result")
    path_str = _extract_video_path(result if isinstance(result, dict) else None)
    if not path_str:
        raise HTTPException(status_code=404, detail="输出路径不可用")

    path = Path(path_str)
    if not path.is_absolute():
        path = (_repo_root() / path).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        path,
        media_type="video/mp4",
        filename=path.name,
    )


@router.get("/templates")
async def get_templates():
    """获取可用模板列表"""
    return [
        {
            "id": "bar_chart_race",
            "name": "柱状图竞赛",
            "description": "排名变化展示",
            "icon": "bi-bar-chart-fill",
        },
        {
            "id": "line_chart_animated",
            "name": "动态折线图",
            "description": "趋势展示",
            "icon": "bi-graph-up",
        },
        {
            "id": "scatter_plot_dynamic",
            "name": "动态散点图",
            "description": "相关性分析",
            "icon": "bi-diagram-3-fill",
        },
        {
            "id": "area_chart_stacked",
            "name": "堆叠面积图",
            "description": "占比变化",
            "icon": "bi-layers-fill",
        },
        {
            "id": "bubble_chart",
            "name": "气泡图",
            "description": "三维数据对比",
            "icon": "bi-circle-fill",
        },
        {
            "id": "bar_chart_horizontal",
            "name": "水平柱状图",
            "description": "对比分析",
            "icon": "bi-bar-chart-line",
        },
    ]


@router.get("/brands")
async def get_brands():
    """获取品牌主题列表"""
    return [
        {
            "id": "default",
            "name": "默认",
            "description": "简洁专业",
            "primaryColor": "#1f77b4",
            "secondaryColor": "#ff7f0e",
            "accentColor": "#2ca02c",
        },
        {
            "id": "corporate",
            "name": "企业",
            "description": "稳重商务",
            "primaryColor": "#003366",
            "secondaryColor": "#0066cc",
            "accentColor": "#0099ff",
        },
        {
            "id": "minimalist",
            "name": "极简",
            "description": "少即是多",
            "primaryColor": "#000000",
            "secondaryColor": "#333333",
            "accentColor": "#666666",
        },
        {
            "id": "vibrant",
            "name": "鲜艳",
            "description": "活力四射",
            "primaryColor": "#FF6B6B",
            "secondaryColor": "#4ECDC4",
            "accentColor": "#45B7D1",
        },
        {
            "id": "new_york_times",
            "name": "纽约时报",
            "description": "经典新闻风格",
            "primaryColor": "#326891",
            "secondaryColor": "#EAECEF",
            "accentColor": "#5F6D7B",
        },
        {
            "id": "financial_times",
            "name": "金融时报",
            "description": "金融专业",
            "primaryColor": "#F27935",
            "secondaryColor": "#00A651",
            "accentColor": "#662D91",
        },
    ]

"""
v2.3 视频生成 API

提供快速创建视频的 HTTP 接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v2", tags=["v2 视频生成"])

# 作业存储
job_store: Dict[str, Dict[str, Any]] = {}
OUTPUT_DIR = Path("runtime/outputs/v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
    """作业状态"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ========== API 端点 ==========

@router.post("/create", response_model=VideoCreateResponse)
async def create_video(
    request: VideoCreateRequest,
    background_tasks: BackgroundTasks
):
    """
    创建视频
    
    流程:
    1. 验证模板
    2. 解析数据
    3. 创建作业
    4. 后台渲染
    """
    # 生成作业 ID
    job_id = str(uuid.uuid4())[:8]
    
    # 创建作业记录
    job = {
        "job_id": job_id,
        "request": request.dict(),
        "status": "pending",
        "progress": 0,
        "message": "准备生成...",
        "created_at": datetime.now(),
        "completed_at": None,
        "output_path": None,
        "error": None
    }
    job_store[job_id] = job
    
    # 后台执行渲染
    background_tasks.add_task(render_video_job, job_id)
    
    return VideoCreateResponse(
        job_id=job_id,
        status="pending",
        message="视频创建成功，正在后台渲染",
        created_at=job["created_at"]
    )


@router.get("/status/{job_id}", response_model=VideoJobStatus)
async def get_job_status(job_id: str):
    """获取作业状态"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="作业不存在")
    
    job = job_store[job_id]
    
    return VideoJobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        output_path=job.get("output_path"),
        error=job.get("error"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """下载生成的视频"""
    from fastapi.responses import FileResponse
    
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="作业不存在")
    
    job = job_store[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="作业未完成")
    
    if not job["output_path"] or not Path(job["output_path"]).exists():
        raise HTTPException(status_code=404, detail="输出文件不存在")
    
    return FileResponse(
        job["output_path"],
        media_type="video/mp4",
        filename=Path(job["output_path"]).name
    )


@router.get("/templates")
async def get_templates():
    """获取可用模板列表"""
    return [
        {
            "id": "bar_chart_race",
            "name": "柱状图竞赛",
            "description": "排名变化展示",
            "icon": "bi-bar-chart-fill"
        },
        {
            "id": "line_chart_animated",
            "name": "动态折线图",
            "description": "趋势展示",
            "icon": "bi-graph-up"
        },
        {
            "id": "scatter_plot_dynamic",
            "name": "动态散点图",
            "description": "相关性分析",
            "icon": "bi-diagram-3-fill"
        },
        {
            "id": "area_chart_stacked",
            "name": "堆叠面积图",
            "description": "占比变化",
            "icon": "bi-layers-fill"
        },
        {
            "id": "bubble_chart",
            "name": "气泡图",
            "description": "三维数据对比",
            "icon": "bi-circle-fill"
        },
        {
            "id": "bar_chart_horizontal",
            "name": "水平柱状图",
            "description": "对比分析",
            "icon": "bi-bar-chart-line"
        }
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
            "accentColor": "#2ca02c"
        },
        {
            "id": "corporate",
            "name": "企业",
            "description": "稳重商务",
            "primaryColor": "#003366",
            "secondaryColor": "#0066cc",
            "accentColor": "#0099ff"
        },
        {
            "id": "minimalist",
            "name": "极简",
            "description": "少即是多",
            "primaryColor": "#000000",
            "secondaryColor": "#333333",
            "accentColor": "#666666"
        },
        {
            "id": "vibrant",
            "name": "鲜艳",
            "description": "活力四射",
            "primaryColor": "#FF6B6B",
            "secondaryColor": "#4ECDC4",
            "accentColor": "#45B7D1"
        },
        {
            "id": "new_york_times",
            "name": "纽约时报",
            "description": "经典新闻风格",
            "primaryColor": "#326891",
            "secondaryColor": "#EAECEF",
            "accentColor": "#5F6D7B"
        },
        {
            "id": "financial_times",
            "name": "金融时报",
            "description": "金融专业",
            "primaryColor": "#F27935",
            "secondaryColor": "#00A651",
            "accentColor": "#662D91"
        }
    ]


# ========== 后台渲染任务 ==========

def render_video_job(job_id: str):
    """后台渲染视频"""
    job = job_store.get(job_id)
    if not job:
        return
    
    try:
        # 更新状态
        job["status"] = "processing"
        job["progress"] = 10
        job["message"] = "准备渲染..."
        
        request = job["request"]
        template_id = request["template"]["template_id"]
        brand_id = request["brand"]["brand_id"]
        data_input = request["data"]
        
        # 解析数据
        job["progress"] = 20
        job["message"] = "解析数据..."
        
        # 兼容处理：支持字符串和数组两种格式
        labels_raw = data_input["labels"]
        values_raw = data_input["values"]
        
        # 如果是字符串，按逗号分割（支持中文逗号和英文逗号）；如果是数组，直接使用
        if isinstance(labels_raw, str):
            # 先替换中文逗号为英文逗号，再分割
            labels_normalized = labels_raw.replace(",", ",").strip()
            labels = [l.strip() for l in labels_normalized.split(",") if l.strip()]
        elif isinstance(labels_raw, list):
            labels = [str(l).strip() for l in labels_raw if str(l).strip()]
        else:
            raise ValueError(f"labels 格式错误：期望字符串或数组，得到 {type(labels_raw)}")
        
        if isinstance(values_raw, str):
            # 先替换中文逗号为英文逗号，再分割
            values_normalized = values_raw.replace(",", ",").strip()
            values = [float(v.strip()) for v in values_normalized.split(",") if v.strip()]
        elif isinstance(values_raw, list):
            values = [float(v) for v in values_raw if v is not None and str(v).strip()]
        else:
            raise ValueError(f"values 格式错误：期望字符串或数组，得到 {type(values_raw)}")
        
        if len(labels) != len(values):
            raise ValueError(f"标签和数值数量不匹配：labels={len(labels)}, values={len(values)}")
        
        # 构建图表数据
        chart_data = {
            "date": labels,
            "category": [data_input.get("series_name", "Series")] * len(labels),
            "value": values
        }
        
        # 使用 v2 渲染器
        job["progress"] = 40
        job["message"] = "渲染图表..."
        
        from core.v2_renderer import render_v2_template
        
        output_filename = f"video_{job_id}.mp4"
        output_path = OUTPUT_DIR / output_filename
        
        # 渲染视频
        video_path = render_v2_template(
            template_name=template_id,
            data=chart_data,
            brand=brand_id,
            platform=request.get("platform", "bilibili"),
            output_path=str(output_path)
        )
        
        # 完成
        job["progress"] = 100
        job["status"] = "completed"
        job["message"] = "视频生成成功"
        job["output_path"] = video_path
        job["completed_at"] = datetime.now()
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["message"] = f"生成失败：{e}"
        job["completed_at"] = datetime.now()

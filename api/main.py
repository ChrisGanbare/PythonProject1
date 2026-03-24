"""
RESTful API 服务 - 视频生成 HTTP API

提供完整的 RESTful 接口用于视频创作
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from pathlib import Path
import uvicorn
import asyncio
from datetime import datetime
import uuid

# 导入核心模块
from core.templates import get_template, list_templates
from core.data.sources import CSVSource, ExcelSource, InlineDataSource, JSONSource
from core.brand import get_theme, list_themes
from core.render import create_renderer


# ========== FastAPI 应用 ==========

app = FastAPI(
    title="PythonProject1 Video API",
    description="数据可视化视频生成 API",
    version="2.1.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 数据模型 ==========

class VideoJobRequest(BaseModel):
    """视频生成请求"""
    
    template: str = Field(..., description="模板名称")
    data_url: Optional[str] = Field(None, description="数据文件 URL")
    data_inline: Optional[Dict] = Field(None, description="内联数据")
    brand: str = Field("default", description="品牌主题")
    output_name: str = Field("output.mp4", description="输出文件名")
    
    # 可选配置
    width: int = Field(1920, description="宽度")
    height: int = Field(1080, description="高度")
    fps: int = Field(30, description="帧率")


class VideoJobResponse(BaseModel):
    """视频生成响应"""
    
    job_id: str
    status: str
    message: str
    output_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TemplateInfo(BaseModel):
    """模板信息"""
    
    name: str
    description: str
    data_schema: Dict[str, Any]


class ThemeInfo(BaseModel):
    """主题信息"""
    
    name: str
    description: str
    colors: Dict[str, str]
    fonts: Dict[str, str]


# ========== 作业存储 ==========

job_store: Dict[str, Dict[str, Any]] = {}
OUTPUT_DIR = Path("runtime/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========== API 端点 ==========

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "PythonProject1 Video API",
        "version": "2.1.0",
        "status": "running",
        "endpoints": {
            "templates": "/api/v1/templates",
            "themes": "/api/v1/themes",
            "jobs": "/api/v1/jobs"
        }
    }


@app.get("/api/v1/templates", response_model=List[str])
async def list_templates_api():
    """列出所有可用模板"""
    templates = list_templates()
    return list(templates.keys())


@app.get("/api/v1/templates/{template_name}")
async def get_template_info(template_name: str):
    """获取模板详情"""
    template = get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    
    return {
        "name": template_name,
        "description": template.config.description,
        "data_schema": {
            "required_columns": template.data_schema.required_columns,
            "optional_columns": template.data_schema.optional_columns
        },
        "config": {
            "chart_type": template.config.chart_type,
            "animation_enabled": template.config.animation_enabled
        }
    }


@app.get("/api/v1/themes", response_model=List[str])
async def list_themes_api():
    """列出所有品牌主题"""
    themes = list_themes()
    return list(themes.keys())


@app.get("/api/v1/themes/{theme_name}")
async def get_theme_info(theme_name: str):
    """获取主题详情"""
    theme = get_theme(theme_name)
    if not theme:
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")
    
    return {
        "name": theme.name,
        "description": theme.description,
        "colors": theme.colors.to_dict(),
        "fonts": theme.fonts.to_dict()
    }


@app.post("/api/v1/jobs", response_model=VideoJobResponse)
async def create_video_job(request: VideoJobRequest, background_tasks: BackgroundTasks):
    """创建视频生成作业"""
    
    # 验证模板
    template = get_template(request.template)
    if not template:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template: {request.template}. Available: {list(list_templates().keys())}"
        )
    
    # 验证品牌
    brand = get_theme(request.brand)
    if not brand:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid brand: {request.brand}. Available: {list(list_themes().keys())}"
        )
    
    # 生成作业 ID
    job_id = str(uuid.uuid4())[:8]
    
    # 创建作业记录
    job = {
        "job_id": job_id,
        "request": request.dict(),
        "status": "pending",
        "created_at": datetime.now(),
        "completed_at": None,
        "output_path": None,
        "error": None
    }
    job_store[job_id] = job
    
    # 后台执行渲染
    background_tasks.add_task(render_video_job, job_id)
    
    return VideoJobResponse(
        job_id=job_id,
        status="pending",
        message="Job created successfully",
        created_at=job["created_at"]
    )


@app.get("/api/v1/jobs/{job_id}", response_model=VideoJobResponse)
async def get_job_status(job_id: str):
    """获取作业状态"""
    
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_store[job_id]
    
    return VideoJobResponse(
        job_id=job["job_id"],
        status=job["status"],
        message=job.get("error", "Success"),
        output_path=job.get("output_path"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@app.get("/api/v1/jobs/{job_id}/download")
async def download_video(job_id: str):
    """下载生成的视频"""
    
    from fastapi.responses import FileResponse
    
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_store[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job["output_path"] or not Path(job["output_path"]).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        job["output_path"],
        media_type="video/mp4",
        filename=Path(job["output_path"]).name
    )


# ========== 后台任务 ==========

def render_video_job(job_id: str):
    """后台渲染视频"""
    
    job = job_store.get(job_id)
    if not job:
        return
    
    try:
        # 更新状态
        job["status"] = "processing"
        
        request = job["request"]
        
        # 1. 加载数据
        if request.get("data_inline"):
            data_source = InlineDataSource(request["data_inline"])
        elif request.get("data_url"):
            # TODO: 支持 URL 下载
            data_source = InlineDataSource({"date": ["2024-01"], "category": ["A"], "value": [100]})
        else:
            raise ValueError("No data provided")
        
        # 2. 获取模板和品牌
        template = get_template(request["template"])
        brand = get_theme(request["brand"])
        
        # 3. 构建视频清单
        manifest = template.build(data_source, brand)
        
        # 4. 渲染视频
        renderer = create_renderer(
            backend="plotly",
            width=request.get("width", 1920),
            height=request.get("height", 1080)
        )
        
        output_path = OUTPUT_DIR / request.get("output_name", f"{job_id}.mp4")
        # TODO: 实际渲染
        # video_path = renderer.render(manifest.to_dict(), str(output_path))
        
        # 模拟渲染（用于测试）
        output_path.touch()
        
        # 5. 更新作业状态
        job["status"] = "completed"
        job["output_path"] = str(output_path)
        job["completed_at"] = datetime.now()
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now()


# ========== CLI 启动命令 ==========

def main():
    """启动 API 服务"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PythonProject1 Video API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    parser.add_argument("--reload", action="store_true", help="Reload on changes")
    
    args = parser.parse_args()
    
    print(f"Starting API server on {args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()

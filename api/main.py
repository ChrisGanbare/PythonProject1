"""
RESTful API 服务 - 视频生成 HTTP API

提供完整的 RESTful 接口用于视频创作，支持:
    - 模板查询与管理
    - 品牌主题管理
    - 视频作业创建与查询
    - 异步后台渲染
    - 视频下载

API 端点:
    GET  /                          - API 根路径
    GET  /api/v1/templates          - 列出所有模板
    GET  /api/v1/templates/{name}   - 获取模板详情
    GET  /api/v1/themes             - 列出所有主题
    GET  /api/v1/themes/{name}      - 获取主题详情
    POST /api/v1/jobs               - 创建视频作业
    GET  /api/v1/jobs/{id}          - 查询作业状态
    GET  /api/v1/jobs/{id}/download - 下载生成的视频

使用示例:
    ```bash
    # 启动 API 服务
    python -m api.main --port 8000
    
    # 创建视频作业
    curl -X POST "http://localhost:8000/api/v1/jobs" \
      -H "Content-Type: application/json" \
      -d '{
        "template": "bar_chart_race",
        "data_inline": {
          "date": ["2024-01", "2024-02"],
          "category": ["A", "B"],
          "value": [100, 200]
        },
        "brand": "corporate"
      }'
    
    # 查询状态
    curl "http://localhost:8000/api/v1/jobs/{job_id}"
    ```
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from pathlib import Path
import uvicorn
import uuid
from datetime import datetime

# 导入核心模块
from core.templates import get_template, list_templates
from core.data.sources import InlineDataSource
from core.brand import get_theme, list_themes
from core.render import create_renderer


# ========== FastAPI 应用 ==========

app = FastAPI(
    title="PythonProject1 Video API",
    description="数据可视化视频生成 API - 提供模板、品牌、渲染等完整能力",
    version="2.2.0",
    docs_url="/docs",  # Swagger UI 地址
    redoc_url="/redoc"  # ReDoc 地址
)

# CORS 中间件 - 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源 (生产环境应限制)
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)


# ========== 数据模型 (Pydantic) ==========

class VideoJobRequest(BaseModel):
    """
    视频生成请求模型
    
    用于接收客户端创建视频作业的请求数据。
    
    属性:
        template: 模板名称 (必需)
        data_url: 数据文件 URL (可选，未来支持)
        data_inline: 内联数据 (可选，与 data_url 二选一)
        brand: 品牌主题名称，默认 "default"
        output_name: 输出文件名，默认 "output.mp4"
        width: 视频宽度，默认 1920
        height: 视频高度，默认 1080
        fps: 帧率，默认 30
    
    验证规则:
        - template 必须提供
        - data_url 和 data_inline 至少提供一个
    """
    
    template: str = Field(..., description="模板名称 (如 bar_chart_race)")
    data_url: Optional[str] = Field(None, description="数据文件 URL")
    data_inline: Optional[Dict] = Field(None, description="内联数据 (JSON 格式)")
    brand: str = Field("default", description="品牌主题名称")
    output_name: str = Field("output.mp4", description="输出文件名")
    
    # 可选配置
    width: int = Field(1920, description="视频宽度 (像素)")
    height: int = Field(1080, description="视频高度 (像素)")
    fps: int = Field(30, description="帧率")


class VideoJobResponse(BaseModel):
    """
    视频生成响应模型
    
    用于返回作业创建和查询的结果。
    
    属性:
        job_id: 作业唯一标识符
        status: 作业状态 (pending/processing/completed/failed)
        message: 状态消息或错误信息
        output_path: 输出文件路径 (完成后)
        created_at: 创建时间
        completed_at: 完成时间 (完成后)
    """
    
    job_id: str
    status: str
    message: str
    output_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TemplateInfo(BaseModel):
    """模板信息模型"""
    name: str
    description: str
    data_schema: Dict[str, Any]


class ThemeInfo(BaseModel):
    """主题信息模型"""
    name: str
    description: str
    colors: Dict[str, str]
    fonts: Dict[str, str]


# ========== 作业存储 (内存) ==========

# 作业存储字典 (生产环境应使用数据库)
job_store: Dict[str, Dict[str, Any]] = {}

# 输出目录
OUTPUT_DIR = Path("runtime/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========== API 端点 ==========

@app.get("/")
async def root():
    """
    API 根路径
    
    返回 API 基本信息和可用端点。
    
    Returns:
        dict: API 名称、版本、状态和端点列表
    """
    return {
        "name": "PythonProject1 Video API",
        "version": "2.2.0",
        "status": "running",
        "endpoints": {
            "templates": "/api/v1/templates",
            "themes": "/api/v1/themes",
            "jobs": "/api/v1/jobs"
        }
    }


@app.get("/api/v1/templates", response_model=List[str])
async def list_templates_api():
    """
    列出所有可用模板
    
    Returns:
        List[str]: 模板名称列表
        
    使用示例:
        ```bash
        curl http://localhost:8000/api/v1/templates
        ```
    """
    templates = list_templates()
    return list(templates.keys())


@app.get("/api/v1/templates/{template_name}")
async def get_template_info(template_name: str):
    """
    获取模板详情
    
    Args:
        template_name: 模板名称
        
    Returns:
        dict: 模板详细信息 (名称、描述、数据模式、配置)
        
    Raises:
        HTTPException: 404 - 模板不存在
        
    使用示例:
        ```bash
        curl http://localhost:8000/api/v1/templates/bar_chart_race
        ```
    """
    template = get_template(template_name)
    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"模板 '{template_name}' 不存在"
        )
    
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
    """
    列出所有品牌主题
    
    Returns:
        List[str]: 主题名称列表
    """
    themes = list_themes()
    return list(themes.keys())


@app.get("/api/v1/themes/{theme_name}")
async def get_theme_info(theme_name: str):
    """
    获取主题详情
    
    Args:
        theme_name: 主题名称
        
    Returns:
        dict: 主题详细信息 (名称、描述、颜色、字体)
        
    Raises:
        HTTPException: 404 - 主题不存在
    """
    theme = get_theme(theme_name)
    if not theme:
        raise HTTPException(
            status_code=404,
            detail=f"主题 '{theme_name}' 不存在"
        )
    
    return {
        "name": theme.name,
        "description": theme.description,
        "colors": theme.colors.to_dict(),
        "fonts": theme.fonts.to_dict()
    }


@app.post("/api/v1/jobs", response_model=VideoJobResponse)
async def create_video_job(request: VideoJobRequest, background_tasks: BackgroundTasks):
    """
    创建视频生成作业
    
    接收视频生成请求，创建后台作业并立即返回作业 ID。
    实际渲染在后台异步执行。
    
    Args:
        request: 视频生成请求
        background_tasks: FastAPI 后台任务管理器
        
    Returns:
        VideoJobResponse: 作业创建响应 (包含 job_id)
        
    Raises:
        HTTPException: 400 - 模板或品牌无效
        
    处理流程:
        1. 验证模板是否存在
        2. 验证品牌是否存在
        3. 生成作业 ID
        4. 创建作业记录
        5. 添加后台渲染任务
        6. 返回作业信息
    
    使用示例:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/jobs" \
          -H "Content-Type: application/json" \
          -d '{
            "template": "bar_chart_race",
            "data_inline": {...},
            "brand": "corporate"
          }'
        ```
    """
    
    # 验证模板
    template = get_template(request.template)
    if not template:
        raise HTTPException(
            status_code=400,
            detail=f"无效的模板：{request.template}"
        )
    
    # 验证品牌
    brand = get_theme(request.brand)
    if not brand:
        raise HTTPException(
            status_code=400,
            detail=f"无效的品牌：{request.brand}"
        )
    
    # 生成作业 ID (8 位 UUID)
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
        message="作业创建成功",
        created_at=job["created_at"]
    )


@app.get("/api/v1/jobs/{job_id}", response_model=VideoJobResponse)
async def get_job_status(job_id: str):
    """
    获取作业状态
    
    Args:
        job_id: 作业 ID
        
    Returns:
        VideoJobResponse: 作业状态信息
        
    Raises:
        HTTPException: 404 - 作业不存在
        
    作业状态:
        - pending: 等待处理
        - processing: 正在渲染
        - completed: 渲染完成
        - failed: 渲染失败
    """
    
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="作业不存在")
    
    job = job_store[job_id]
    
    return VideoJobResponse(
        job_id=job["job_id"],
        status=job["status"],
        message=job.get("error", "成功"),
        output_path=job.get("output_path"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@app.get("/api/v1/jobs/{job_id}/download")
async def download_video(job_id: str):
    """
    下载生成的视频
    
    Args:
        job_id: 作业 ID
        
    Returns:
        FileResponse: 视频文件
        
    Raises:
        HTTPException:
            404 - 作业不存在或文件不存在
            400 - 作业未完成
    
    使用示例:
        ```bash
        curl "http://localhost:8000/api/v1/jobs/{job_id}/download" -o output.mp4
        ```
    """
    
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


# ========== 后台任务 ==========

def render_video_job(job_id: str):
    """
    后台渲染视频作业
    
    在后台异步执行视频渲染流程。
    
    处理流程:
        1. 获取作业信息
        2. 更新状态为 processing
        3. 加载数据 (内联或 URL)
        4. 获取模板和品牌
        5. 构建视频清单
        6. 渲染视频
        7. 更新作业状态
    
    Args:
        job_id: 作业 ID
        
    异常处理:
        任何异常都会导致作业状态变为 failed，并记录错误信息
    """
    
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
            raise ValueError("未提供数据")
        
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
        
        # 模拟渲染 (用于测试)
        output_path.touch()
        
        # 5. 更新作业状态
        job["status"] = "completed"
        job["output_path"] = str(output_path)
        job["completed_at"] = datetime.now()
        
    except Exception as e:
        # 记录错误
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.now()


# ========== CLI 启动命令 ==========

def main():
    """
    启动 API 服务
    
    使用命令行参数启动 UVicorn 服务器。
    
    使用示例:
        ```bash
        # 默认配置 (0.0.0.0:8000)
        python -m api.main
        
        # 自定义端口
        python -m api.main --port 8080
        
        # 开发模式 (热重载)
        python -m api.main --reload
        ```
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="PythonProject1 Video API Server")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="文件变更时自动重载")
    
    args = parser.parse_args()
    
    print(f"启动 API 服务器于 {args.host}:{args.port}")
    print(f"API 文档：http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()

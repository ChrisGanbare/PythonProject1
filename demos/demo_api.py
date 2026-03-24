"""
API 服务演示 - 测试 RESTful API
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_platform_specs():
    """演示平台规格"""
    print("\n" + "="*70)
    print("平台规格演示")
    print("="*70)
    
    from platforms import list_platforms, get_platform_spec
    
    # 列出所有平台
    platforms = list_platforms()
    print(f"\n支持平台：{len(platforms)} 个")
    
    for name, spec in platforms.items():
        print(f"  • {spec.name}")
        print(f"    分辨率：{spec.resolution[0]}x{spec.resolution[1]}")
        print(f"    比例：{spec.aspect_ratio}")
        print(f"    最大时长：{spec.max_duration}s")
    
    # 获取具体平台
    bilibili = get_platform_spec("bilibili")
    print(f"\n✓ B 站规格详情:")
    print(f"  分辨率：{bilibili.resolution}")
    print(f"  码率：{bilibili.bitrate}")
    print(f"  封面：{bilibili.cover_resolution}")
    
    douyin = get_platform_spec("douyin")
    print(f"\n✓ 抖音规格详情:")
    print(f"  分辨率：{douyin.resolution} (竖屏)")
    print(f"  字幕安全区：底部 {douyin.subtitle_safe_area['bottom']}px")
    
    return True


def demo_api_usage():
    """演示 API 使用"""
    print("\n" + "="*70)
    print("API 使用示例")
    print("="*70)
    
    print("""
# 1. 启动 API 服务
python -m api.main --port 8000

# 2. 查看 API 文档
# 浏览器访问：http://localhost:8000/docs

# 3. 创建视频作业 (curl)
curl -X POST "http://localhost:8000/api/v1/jobs" \\
  -H "Content-Type: application/json" \\
  -d '{
    "template": "bar_chart_race",
    "data_inline": {
      "date": ["2024-01", "2024-02"],
      "category": ["A", "B"],
      "value": [100, 200]
    },
    "brand": "corporate",
    "output_name": "my_video.mp4"
  }'

# 4. 查询作业状态
curl "http://localhost:8000/api/v1/jobs/{job_id}"

# 5. 下载视频
curl "http://localhost:8000/api/v1/jobs/{job_id}/download" -o output.mp4

# 6. Python 客户端
import requests

# 创建作业
response = requests.post("http://localhost:8000/api/v1/jobs", json={
    "template": "bar_chart_race",
    "data_inline": {...},
    "brand": "corporate"
})
job_id = response.json()["job_id"]

# 等待完成
import time
while True:
    response = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
    status = response.json()["status"]
    if status == "completed":
        break
    time.sleep(1)

# 下载视频
response = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}/download")
with open("output.mp4", "wb") as f:
    f.write(response.content)
    """)
    
    print("\n  ✓ API 示例已展示")
    return True


def demo_templates_and_themes():
    """演示模板和主题 API"""
    print("\n" + "="*70)
    print("模板与主题 API")
    print("="*70)
    
    from core.templates import list_templates, get_template
    from core.brand import list_themes, get_theme
    
    # 模板
    templates = list_templates()
    print(f"\n可用模板 ({len(templates)} 个):")
    for name in sorted(templates.keys()):
        template = get_template(name)
        print(f"  • {name}: {template.config.chart_type}")
    
    # 主题
    themes = list_themes()
    print(f"\n可用主题 ({len(themes)} 个):")
    for name in sorted(themes.keys()):
        theme = get_theme(name)
        print(f"  • {name}: {theme.colors.primary}")
    
    return True


def demo_integration_example():
    """演示集成示例"""
    print("\n" + "="*70)
    print("集成示例：完整工作流")
    print("="*70)
    
    print("""
from core.templates import get_template
from core.data.sources import CSVSource
from core.brand import get_theme
from core.render import create_renderer
from platforms import get_platform_spec

# 1. 选择平台
platform = get_platform_spec("bilibili")
print(f"目标平台：{platform.name}")
print(f"分辨率：{platform.resolution}")

# 2. 准备数据
data = CSVSource("sales_data.csv")

# 3. 选择模板
template = get_template("bar_chart_race")

# 4. 选择品牌
brand = get_theme("corporate")

# 5. 构建清单
manifest = template.build(data, brand)

# 6. 渲染（符合平台规格）
renderer = create_renderer(
    backend="plotly",
    width=platform.resolution[0],
    height=platform.resolution[1]
)

video_path = renderer.render(manifest.to_dict(), "bilibili_output.mp4")

# 7. 验证
from platforms import validate_for_platform
is_valid, issues = validate_for_platform(video_path, "bilibili")
if is_valid:
    print("✓ 视频符合平台要求")
else:
    print("✗ 问题:", issues)
    """)
    
    print("\n  ✓ 集成示例已展示")
    return True


def main():
    """主函数"""
    print("\n" + "#"*70)
    print("# PythonProject1 v2.2 - API 与平台集成演示")
    print("#"*70)
    
    try:
        demo_platform_specs()
        demo_templates_and_themes()
        demo_api_usage()
        demo_integration_example()
        
        print("\n" + "="*70)
        print("✅ 所有演示完成!")
        print("="*70)
        
        print("\n📊 v2.2 新能力:")
        print("  ✓ RESTful API - 完整的 HTTP 接口")
        print("  ✓ 平台规格 - 6 个平台支持")
        print("  ✓ 自动验证 - 视频合规检查")
        print("  ✓ 后台作业 - 异步渲染")
        
        print("\n🎯 平台支持:")
        print("  • 哔哩哔哩 (16:9 横屏)")
        print("  • 抖音 (9:16 竖屏)")
        print("  • 小红书 (9:16 竖屏)")
        print("  • YouTube (16:9 横屏)")
        print("  • Instagram Reels (9:16)")
        print("  • TikTok (9:16)")
        
        print("\n🚀 下一步:")
        print("  1. 启动 API: python -m api.main")
        print("  2. 查看文档：http://localhost:8000/docs")
        print("  3. 创建视频：POST /api/v1/jobs")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
PythonProject1 POC 主入口

演示功能:
1. Plotly 图表生成
2. 摄像机动画
3. 视频合成
"""

import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from visualizer.plotly_viz import PlotlyVisualizer, ChartConfig, quick_line
from camera.controller import CameraController, Camera3DController, create_zoom_animation
from video.composer import VideoComposer, VideoConfig, VideoProcessor


def demo_visualizer():
    """演示可视化模块"""
    print("\n" + "="*50)
    print("1. 可视化模块演示")
    print("="*50)
    
    # 创建图表配置
    config = ChartConfig("line")
    config.set_data(
        x=list(range(10)),
        y=[i**2 for i in range(10)],
        name="Quadratic"
    )
    config.set_layout(
        title="POC Chart Demo",
        xaxis_title="X Axis",
        yaxis_title="Y Axis"
    )
    config.enable_animation(duration=1000)
    
    # 创建可视化器并生成图表
    viz = PlotlyVisualizer(width=800, height=600)
    fig = viz.create_chart(config)
    
    # 保存为 HTML (交互式)
    viz.save_as_html("poc_chart.html")
    
    # 保存为 PNG (静态)
    try:
        viz.save_as_image("poc_chart.png", format="png")
    except Exception as e:
        print(f"Note: Image export requires kaleido: {e}")
    
    print("✓ 图表已生成：poc_chart.html")
    return True


def demo_camera():
    """演示摄像机模块"""
    print("\n" + "="*50)
    print("2. 摄像机模块演示")
    print("="*50)
    
    # 基础摄像机控制
    cam = CameraController()
    cam.set_position(0, 0, 0)
    cam.zoom_to(1.0)
    cam.add_keyframe(0)
    
    cam.set_position(5, 3, 0)
    cam.zoom_to(2.0)
    cam.add_keyframe(3)
    
    # 获取中间状态
    state = cam.get_state_at_time(1.5)
    print(f"  1.5s 时状态：位置={state.position}, 缩放={state.zoom}")
    
    # 3D 摄像机
    cam3d = Camera3DController()
    cam3d.orbit(
        center=np.array([0, 0, 0]),
        radius=5,
        phi=60,
        theta=45
    )
    print(f"  3D 位置：{cam3d.current_state.position}")
    
    # 生成动画帧
    frames = cam.create_camera_animation(duration=3.0)
    print(f"  生成动画帧数：{len(frames)}")
    
    print("✓ 摄像机动画已配置")
    return True


def demo_video():
    """演示视频模块"""
    print("\n" + "="*50)
    print("3. 视频处理模块演示")
    print("="*50)
    
    # 创建视频配置
    config = VideoConfig(
        width=1280,
        height=720,
        fps=30,
        duration=5
    )
    
    # 创建合成器
    composer = VideoComposer(config)
    composer.set_background((20, 20, 40))  # 深蓝色背景
    
    # 添加文字
    composer.add_text(
        text="PythonProject1 POC",
        duration=5,
        font_size=48,
        color="white",
        position="center"
    )
    
    composer.add_text(
        text="Video Generation System",
        duration=5,
        font_size=32,
        color="#AAAAAA",
        position=("center", "center+100")
    )
    
    print("  视频配置：1280x720 @ 30fps, 5 秒")
    print("  背景：深蓝色")
    print("  文字：标题 + 副标题")
    
    # 尝试导出 (需要 MoviePy)
    try:
        composer.compose()
        output = composer.export("poc_video.mp4", preset="fast")
        print(f"✓ 视频已导出：{output}")
    except Exception as e:
        print(f"  视频导出需要 MoviePy 和 FFmpeg")
        print(f"  安装：pip install moviepy imageio-ffmpeg")
        print(f"  错误：{e}")
    
    return True


def demo_integration():
    """演示集成工作流"""
    print("\n" + "="*50)
    print("4. 集成工作流演示")
    print("="*50)
    
    # 步骤 1: 生成图表
    print("  步骤 1: 生成数据图表...")
    fig = quick_line(
        x=list(range(20)),
        y=[i * 2 + 5 for i in range(20)],
        title="Integration Demo",
        save_path="integration_chart.html"  # 改为 HTML 避免 kaleido 依赖
    )
    print("  ✓ 图表生成完成")
    
    # 步骤 2: 配置摄像机动画
    print("  步骤 2: 配置摄像机动画...")
    cam = create_zoom_animation(
        start_zoom=1.0,
        end_zoom=1.5,
        duration=3.0
    )
    frames = cam.create_camera_animation(duration=3.0)
    print(f"  ✓ 生成 {len(frames)} 帧动画")
    
    # 步骤 3: 准备视频合成
    print("  步骤 3: 准备视频合成...")
    config = VideoConfig(width=1280, height=720, fps=30, duration=3)
    composer = VideoComposer(config)
    composer.set_background((25, 25, 35))
    print("  ✓ 合成器就绪")
    
    print("\n✓ 集成工作流演示完成")
    return True


def main():
    """主函数"""
    print("\n" + "#"*50)
    print("# PythonProject1 POC - 视频生成系统原型")
    print("#"*50)
    
    # 导入 numpy (用于 3D 演示)
    global np
    import numpy as np
    
    try:
        # 运行所有演示
        demo_visualizer()
        demo_camera()
        demo_video()
        demo_integration()
        
        print("\n" + "="*50)
        print("✅ 所有 POC 演示完成!")
        print("="*50)
        print("\n生成的文件:")
        print("  - poc_chart.html (交互式图表)")
        print("  - poc_chart.png (静态图表)")
        print("  - integration_chart.png (集成示例)")
        print("  - poc_video.mp4 (视频输出，如 MoviePy 可用)")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

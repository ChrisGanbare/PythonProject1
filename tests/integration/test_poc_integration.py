"""
POC 集成测试

验证 POC 模块在主项目中正常工作
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSharedVisualization:
    """测试共享可视化模块"""
    
    def test_import_visualization(self):
        """测试导入可视化模块"""
        from shared.render.visualization import PlotlyVisualizer, ChartConfig
        assert PlotlyVisualizer is not None
        assert ChartConfig is not None
    
    def test_chart_config(self):
        """测试图表配置"""
        from shared.render.visualization import ChartConfig
        
        config = ChartConfig("line")
        config.set_data(x=[1, 2, 3], y=[4, 5, 6])
        config.set_layout(title="Test Chart")
        
        assert config.chart_type == "line"
        assert config.data['x'] == [1, 2, 3]
        assert config.layout['title'] == "Test Chart"
    
    def test_visualizer(self):
        """测试可视化器"""
        from shared.render.visualization import PlotlyVisualizer, ChartConfig
        
        viz = PlotlyVisualizer(width=800, height=600)
        config = ChartConfig("scatter")
        config.set_data(x=[1, 2], y=[3, 4])
        
        fig = viz.create_chart(config)
        assert fig is not None
        assert len(fig.data) == 1


class TestCoreCamera:
    """测试核心摄像机模块"""
    
    def test_import_camera(self):
        """测试导入摄像机模块"""
        from core.camera import CameraController, CameraState
        assert CameraController is not None
        assert CameraState is not None
    
    def test_camera_controller(self):
        """测试摄像机控制器"""
        from core.camera import CameraController
        
        cam = CameraController()
        cam.set_position(5, 10, 0)
        cam.zoom_in(2.0)
        
        assert cam.current_state.position[0] == 5
        assert cam.current_state.zoom == 2.0
    
    def test_keyframe_animation(self):
        """测试关键帧动画"""
        from core.camera import CameraController
        
        cam = CameraController()
        cam.set_position(0, 0, 0).add_keyframe(0)
        cam.set_position(10, 0, 0).add_keyframe(2)
        
        state = cam.get_state_at_time(1.0)
        assert 4 < state.position[0] < 6
    
    def test_manim_adapter_import(self):
        """测试 Manim 适配器导入"""
        try:
            from core.camera import ManimCameraAdapter, MANIM_AVAILABLE
            assert ManimCameraAdapter is not None
        except ImportError:
            pytest.skip("Manim not installed")


class TestCoreAnimation:
    """测试核心动画引擎模块"""
    
    def test_import_animation(self):
        """测试导入动画模块"""
        from core.animation import Timeline, EasingLibrary
        assert Timeline is not None
        assert EasingLibrary is not None
    
    def test_easing_library(self):
        """测试缓动函数库"""
        from core.animation import EasingLibrary
        
        easings = EasingLibrary.list_functions()
        assert len(easings) >= 30
        
        # 测试几个缓动函数
        assert EasingLibrary.linear(0.5) == 0.5
        assert 0 < EasingLibrary.ease_in_quad(0.5) < 1
    
    def test_timeline(self):
        """测试时间轴"""
        from core.animation import Timeline
        
        timeline = Timeline(fps=60)
        channel = timeline.add_channel("test_obj")
        channel.animate('x', 0, 100, duration=2.0, easing='ease_in_out_quad')
        
        assert timeline.duration == 2.0
        assert len(timeline.channels) == 1
        
        frames = timeline.get_frames()
        assert len(frames) > 0
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        from core.animation import (
            create_fade_animation,
            create_move_animation,
            create_scale_animation
        )
        
        fade = create_fade_animation("obj1", 0, 1, 1.0)
        assert fade.duration == 1.0
        
        move = create_move_animation("obj2", (0, 0), (100, 50), 2.0)
        assert move.duration == 2.0
        
        scale = create_scale_animation("obj3", 1.0, 2.0, 1.0)
        assert scale.duration == 1.0


class TestCoreVideo:
    """测试核心视频模块"""
    
    def test_import_video(self):
        """测试导入视频模块"""
        from core.video import VideoComposer, VideoConfig
        assert VideoComposer is not None
        assert VideoConfig is not None
    
    def test_video_config(self):
        """测试视频配置"""
        from core.video import VideoConfig
        
        config = VideoConfig(width=1920, height=1080, fps=60)
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 60
    
    def test_video_composer(self):
        """测试视频合成器"""
        from core.video import VideoComposer, VideoConfig
        
        config = VideoConfig()
        composer = VideoComposer(config)
        
        assert composer.config == config
        assert len(composer.clips) == 0
        
        # 测试链式调用
        result = composer.set_background((0, 0, 0))
        assert result is composer
    
    def test_ffmpeg_wrapper_import(self):
        """测试 FFmpeg 封装导入"""
        try:
            from core.video import FFmpegWrapper
            ffmpeg = FFmpegWrapper()
            assert ffmpeg is not None
        except ImportError:
            pytest.skip("FFmpeg wrapper not available")


class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建图表
        from shared.render.visualization import ChartConfig, PlotlyVisualizer
        
        config = ChartConfig("line")
        config.set_data(x=[1, 2, 3], y=[1, 4, 9])
        viz = PlotlyVisualizer()
        fig = viz.create_chart(config)
        assert fig is not None
        
        # 2. 创建摄像机动画
        from core.camera import CameraController
        
        cam = CameraController()
        cam.add_keyframe(0)
        cam.zoom_to(2.0).add_keyframe(2)
        frames = cam.create_camera_animation(duration=2)
        assert len(frames) > 0
        
        # 3. 创建动画时间轴
        from core.animation import Timeline
        
        timeline = Timeline(fps=30)
        channel = timeline.add_channel("chart")
        channel.animate('opacity', 0, 1, duration=1.0)
        assert timeline.duration == 1.0
        
        # 4. 准备视频合成
        from core.video import VideoConfig, VideoComposer
        
        v_config = VideoConfig(width=1280, height=720)
        composer = VideoComposer(v_config)
        assert composer is not None
        
        print("✓ 完整工作流测试通过")
    
    def test_performance(self):
        """性能测试"""
        import time
        from core.animation import Timeline
        
        # 创建大量对象的动画
        timeline = Timeline(fps=60)
        num_objects = 100
        
        for i in range(num_objects):
            ch = timeline.add_channel(f"obj_{i}")
            ch.animate('x', 0, i * 10, duration=5.0)
            ch.animate('y', 0, i * 5, duration=5.0)
        
        # 测试帧生成性能
        start = time.time()
        frames = timeline.get_frames(0, 5.0)
        elapsed = time.time() - start
        
        fps_actual = len(frames) / elapsed if elapsed > 0 else 0
        
        print(f"性能测试：{len(frames)} 帧，{elapsed:.3f}s, {fps_actual:.1f} FPS")
        
        # 应该达到至少 1000 FPS (本地处理，无渲染)
        assert fps_actual > 1000, f"Performance too low: {fps_actual} FPS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

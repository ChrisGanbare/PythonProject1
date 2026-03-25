"""
POC 测试套件

测试范围:
1. 可视化模块
2. 摄像机模块
3. 视频处理模块
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPlotlyVisualizer:
    """可视化模块测试"""
    
    def test_chart_config_creation(self):
        """测试图表配置创建"""
        from visualizer.plotly_viz import ChartConfig
        
        config = ChartConfig("scatter")
        assert config.chart_type == "scatter"
        assert config.animation["enabled"] == False
    
    def test_chart_config_chain(self):
        """测试链式调用"""
        from visualizer.plotly_viz import ChartConfig
        
        config = (ChartConfig("line")
                  .set_data(x=[1,2,3], y=[4,5,6])
                  .set_layout(title="Test")
                  .enable_animation(duration=2000))
        
        assert config.data['x'] == [1, 2, 3]
        assert config.layout['title'] == "Test"
        assert config.animation['enabled'] == True
    
    def test_visualizer_creation(self):
        """测试可视化器创建"""
        from visualizer.plotly_viz import PlotlyVisualizer, ChartConfig
        
        viz = PlotlyVisualizer(width=800, height=600)
        config = ChartConfig("scatter")
        config.set_data(x=[1,2], y=[3,4])
        
        fig = viz.create_chart(config)
        assert fig is not None
        assert len(fig.data) == 1


class TestCameraController:
    """摄像机模块测试"""
    
    def test_camera_init(self):
        """测试摄像机初始化"""
        from camera.controller import CameraController
        
        cam = CameraController()
        assert cam.current_state.zoom == 1.0
        assert len(cam.keyframes) == 0
    
    def test_camera_position(self):
        """测试位置设置"""
        from camera.controller import CameraController
        
        cam = CameraController()
        cam.set_position(5, 10, 0)
        
        assert cam.current_state.position[0] == 5
        assert cam.current_state.position[1] == 10
    
    def test_camera_zoom(self):
        """测试缩放"""
        from camera.controller import CameraController
        
        cam = CameraController()
        cam.zoom_in(2.0)
        
        assert cam.current_state.zoom == 2.0
        
        cam.zoom_out(2.0)
        assert cam.current_state.zoom == 1.0
    
    def test_keyframe_animation(self):
        """测试关键帧动画"""
        from camera.controller import CameraController
        
        cam = CameraController()
        cam.set_position(0, 0, 0).add_keyframe(0)
        cam.set_position(10, 0, 0).add_keyframe(2)
        
        # 中间状态应该是插值
        state = cam.get_state_at_time(1.0)
        assert 4 < state.position[0] < 6  # 应该在 5 附近
    
    def test_3d_camera(self):
        """测试 3D 摄像机"""
        from camera.controller import Camera3DController
        import numpy as np
        
        cam = Camera3DController()
        cam.orbit(np.array([0, 0, 0]), 5, 60, 45)
        
        # 位置应该在球面上
        pos = cam.current_state.position
        distance = np.linalg.norm(pos)
        assert 4.9 < distance < 5.1


class TestVideoComposer:
    """视频合成模块测试"""
    
    def test_video_config(self):
        """测试视频配置"""
        from video.composer import VideoConfig
        
        config = VideoConfig(width=1920, height=1080, fps=60)
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 60
    
    def test_composer_creation(self):
        """测试合成器创建"""
        from video.composer import VideoComposer, VideoConfig
        
        config = VideoConfig()
        composer = VideoComposer(config)
        
        assert composer.config == config
        assert len(composer.clips) == 0
    
    def test_composer_chain(self):
        """测试合成器链式调用"""
        from video.composer import VideoComposer, VideoConfig
        
        config = VideoConfig(duration=5)
        composer = VideoComposer(config)
        
        # 链式调用应该返回自身
        result = composer.set_background((0, 0, 0))
        assert result is composer


class TestIntegration:
    """集成测试"""
    
    def test_workflow(self):
        """测试完整工作流"""
        from visualizer.plotly_viz import ChartConfig, PlotlyVisualizer
        from camera.controller import CameraController
        from video.composer import VideoConfig, VideoComposer
        
        # 1. 创建图表
        config = ChartConfig("line")
        config.set_data(x=[1,2,3], y=[1,4,9])
        viz = PlotlyVisualizer()
        fig = viz.create_chart(config)
        assert fig is not None
        
        # 2. 配置摄像机
        cam = CameraController()
        cam.add_keyframe(0)
        cam.zoom_to(2.0).add_keyframe(2)
        frames = cam.create_camera_animation(duration=2)
        assert len(frames) > 0
        
        # 3. 准备视频合成
        v_config = VideoConfig(width=800, height=600)
        composer = VideoComposer(v_config)
        assert composer is not None
        
        print("✓ 集成工作流测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

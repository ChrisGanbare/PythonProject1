"""
Manim 摄像机适配器

将 Manim 的摄像机系统与现有 CameraController 集成

功能:
- Manim Camera API 封装
- Scene 渲染管理
- 坐标系转换
- 高质量视频输出
"""

import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import subprocess
import tempfile
import os

# 尝试导入 Manim
try:
    from manim import (
        Scene, 
        Camera, 
        Mobject,
        ThreeDScene,
        config,
        WHITE,
        BLACK,
        BLUE,
        RED,
        GREEN,
        Circle,
        Square,
        Dot,
        Text,
        Create,
        Write,
        FadeIn,
        FadeOut,
        Transform,
        Wait
    )
    from manim.camera.camera import Camera as ManimCamera
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False
    print("Warning: Manim not installed. Some features disabled.")
    print("Install: pip install manim")


@dataclass
class ManimConfig:
    """Manim 配置"""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    background_color: str = "#000000"
    background_opacity: float = 1.0
    pixel_width: int = 1920
    pixel_height: int = 1080
    frame_rate: float = 30.0
    
    # 渲染质量
    quality: str = "high_quality"  # low, medium, high, high_quality
    renderer: str = "cairo"  # cairo, opengl
    
    # 输出设置
    output_format: str = "mp4"  # mp4, mov, gif
    
    def to_manim_config(self) -> dict:
        """转换为 Manim 配置字典"""
        return {
            "frame_width": self.width / 100,  # Manim 使用不同的单位
            "frame_height": self.height / 100,
            "fps": self.fps,
            "background_color": self.background_color,
            "background_opacity": self.background_opacity,
            "pixel_width": self.pixel_width,
            "pixel_height": self.pixel_height,
            "frame_rate": self.frame_rate,
        }


class ManimCameraAdapter:
    """
    Manim 摄像机适配器
    
    将自研 CameraController 与 Manim Camera 桥接
    """
    
    def __init__(self, config: Optional[ManimConfig] = None):
        if config is None:
            config = ManimConfig()
        self.config = config
        self.scene: Optional[Scene] = None
        self.camera: Optional[ManimCamera] = None
        self.mobjects: List[Mobject] = []
        
        if MANIM_AVAILABLE:
            self._apply_config()
    
    def _apply_config(self):
        """应用 Manim 配置"""
        if not MANIM_AVAILABLE:
            return
        
        # 设置 Manim 全局配置
        config.pixel_width = self.config.pixel_width
        config.pixel_height = self.config.pixel_height
        config.frame_rate = self.config.frame_rate
        config.background_color = self.config.background_color
        
        # 质量预设
        quality_presets = {
            "low": {"pixel_width": 854, "pixel_height": 480},
            "medium": {"pixel_width": 1280, "pixel_height": 720},
            "high": {"pixel_width": 1920, "pixel_height": 1080},
            "high_quality": {"pixel_width": 3840, "pixel_height": 2160}
        }
        
        if self.config.quality in quality_presets:
            preset = quality_presets[self.config.quality]
            config.pixel_width = preset["pixel_width"]
            config.pixel_height = preset["pixel_height"]
    
    def set_scene(self, scene: Scene):
        """设置当前场景"""
        self.scene = scene
        if scene is not None:
            self.camera = scene.camera
    
    def sync_camera_state(self, camera_controller_state) -> 'ManimCameraAdapter':
        """
        同步摄像机状态
        
        Args:
            camera_controller_state: CameraState 对象
            
        Returns:
            self
        """
        if not MANIM_AVAILABLE or self.camera is None:
            return self
        
        state = camera_controller_state
        
        # 设置位置
        # Manim 使用不同的坐标系，需要转换
        self.camera.frame.move_to(state.position[:2])  # 2D 位置
        
        # 设置缩放 (通过帧宽度)
        frame_width = self.config.width / (state.zoom * 100)
        self.camera.frame.set_width(frame_width)
        
        # 设置旋转
        if len(state.rotation) >= 3:
            phi, theta, gamma = state.rotation[:3]
            if isinstance(self.scene, ThreeDScene):
                self.scene.set_camera_orientation(
                    phi=phi * np.pi / 180,
                    theta=theta * np.pi / 180,
                    gamma=gamma * np.pi / 180
                )
        
        return self
    
    def add_mobject(self, mobject: Mobject) -> 'ManimCameraAdapter':
        """添加数学对象到场景"""
        if not MANIM_AVAILABLE:
            return self
        
        self.mobjects.append(mobject)
        if self.scene:
            self.scene.add(mobject)
        return self
    
    def create_text(self, text: str, **kwargs) -> Optional[Mobject]:
        """
        创建文字对象
        
        Args:
            text: 文字内容
            **kwargs: Text 参数 (font_size, color, etc.)
        """
        if not MANIM_AVAILABLE:
            print(f"Would create text: {text}")
            return None
        
        try:
            text_obj = Text(text, **kwargs)
            return text_obj
        except Exception as e:
            print(f"Warning: Could not create text: {e}")
            return None
    
    def create_shape(self, shape_type: str, **kwargs) -> Optional[Mobject]:
        """
        创建几何形状
        
        Args:
            shape_type: 形状类型 ('circle', 'square', 'dot', 'rectangle')
            **kwargs: 形状参数
        """
        if not MANIM_AVAILABLE:
            print(f"Would create shape: {shape_type}")
            return None
        
        shape_type = shape_type.lower()
        
        if shape_type == 'circle':
            return Circle(**kwargs)
        elif shape_type == 'square':
            return Square(**kwargs)
        elif shape_type == 'dot':
            return Dot(**kwargs)
        elif shape_type == 'rectangle':
            from manim import Rectangle
            return Rectangle(**kwargs)
        else:
            print(f"Unknown shape type: {shape_type}")
            return None
    
    def render_scene(self, 
                     output_path: str,
                     scene_class: type = None,
                     duration: float = 5.0) -> str:
        """
        渲染场景到视频
        
        Args:
            output_path: 输出文件路径
            scene_class: Scene 类 (None 使用当前场景)
            duration: 时长 (秒)
            
        Returns:
            输出文件路径
        """
        if not MANIM_AVAILABLE:
            print(f"Would render scene to: {output_path}")
            return output_path
        
        # 如果没有提供场景类，创建一个简单的
        if scene_class is None:
            scene_class = self._create_default_scene()
        
        # 使用命令行渲染
        temp_file = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
        
        # 写入场景代码
        scene_code = self._generate_scene_code(scene_class, duration)
        temp_file.write(scene_code.encode())
        temp_file.close()
        
        # 构建渲染命令
        cmd = [
            'manim',
            '-qh',  # 高质量
            '--format=mp4',
            temp_file.name,
            scene_class.__name__,
            '-o', output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"Manim render error: {result.stderr}")
                raise RuntimeError(f"Manim rendering failed: {result.stderr}")
            
            print(f"Rendered scene to: {output_path}")
            
        except subprocess.TimeoutExpired:
            print("Manim rendering timed out")
            raise
        finally:
            # 清理临时文件
            os.unlink(temp_file.name)
        
        return output_path
    
    def _create_default_scene(self):
        """创建默认场景类"""
        if not MANIM_AVAILABLE:
            return None
        
        adapter = self
        
        class DefaultScene(Scene):
            def construct(self):
                # 添加适配器中的对象
                for mobject in adapter.mobjects:
                    self.add(mobject)
                
                # 简单动画
                if adapter.mobjects:
                    self.play(FadeIn(adapter.mobjects[0]))
                    self.wait(2)
                    self.play(FadeOut(adapter.mobjects[0]))
        
        return DefaultScene
    
    def _generate_scene_code(self, scene_class: type, duration: float) -> str:
        """生成场景代码"""
        class_name = scene_class.__name__
        
        code = f'''
from manim import *

config.pixel_width = {self.config.pixel_width}
config.pixel_height = {self.config.pixel_height}
config.frame_rate = {self.config.frame_rate}
config.background_color = "{self.config.background_color}"

class {class_name}(Scene):
    def construct(self):
        # Auto-generated scene
        self.wait({duration})
'''
        return code
    
    def reset(self) -> 'ManimCameraAdapter':
        """重置适配器"""
        self.mobjects = []
        if self.scene:
            self.scene.clear()
        return self


class ManimSceneRenderer:
    """
    Manim 场景渲染器
    
    高级场景管理和渲染
    """
    
    def __init__(self, config: Optional[ManimConfig] = None):
        self.config = config or ManimConfig()
        self.adapter = ManimCameraAdapter(self.config)
        self.scenes: List[Scene] = []
    
    def create_scene(self, name: str = "Scene") -> Scene:
        """
        创建新场景
        
        Args:
            name: 场景名称
            
        Returns:
            Scene 对象
        """
        if not MANIM_AVAILABLE:
            print(f"Would create scene: {name}")
            return None
        
        class CustomScene(Scene):
            pass
        
        CustomScene.__name__ = name
        self.scenes.append(CustomScene)
        return CustomScene()
    
    def create_3d_scene(self, name: str = "Scene3D") -> ThreeDScene:
        """
        创建 3D 场景
        
        Args:
            name: 场景名称
            
        Returns:
            ThreeDScene 对象
        """
        if not MANIM_AVAILABLE:
            print(f"Would create 3D scene: {name}")
            return None
        
        class Custom3DScene(ThreeDScene):
            pass
        
        Custom3DScene.__name__ = name
        self.scenes.append(Custom3DScene)
        return Custom3DScene()
    
    def render(self, scene: Scene, output_path: str) -> str:
        """
        渲染场景
        
        Args:
            scene: 场景对象
            output_path: 输出路径
            
        Returns:
            输出文件路径
        """
        self.adapter.set_scene(scene)
        return self.adapter.render_scene(
            output_path,
            scene_class=type(scene)
        )
    
    def quick_demo(self, output_path: str = "manim_demo.mp4") -> str:
        """
        快速演示
        
        Args:
            output_path: 输出路径
            
        Returns:
            输出文件路径
        """
        if not MANIM_AVAILABLE:
            print(f"Would render demo to: {output_path}")
            return output_path
        
        # 创建演示场景
        class DemoScene(Scene):
            def construct(self):
                # 创建对象
                circle = Circle(radius=2, color=BLUE)
                square = Square(side_length=3, color=RED)
                
                # 动画
                self.play(Create(circle))
                self.wait(1)
                self.play(Transform(circle, square))
                self.wait(1)
                self.play(FadeOut(circle))
                self.wait(0.5)
        
        return self.adapter.render_scene(output_path, DemoScene)


# 便捷函数
def quick_manim_scene(text: str = "Hello Manim", 
                      output_path: str = "quick_scene.mp4") -> str:
    """
    快速创建简单场景
    
    Args:
        text: 显示文字
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    if not MANIM_AVAILABLE:
        print(f"Would create scene with text: {text}")
        print(f"Output: {output_path}")
        return output_path
    
    class QuickScene(Scene):
        def construct(self):
            text_obj = Text(text, font_size=72)
            self.play(Write(text_obj))
            self.wait(1)
            self.play(FadeOut(text_obj))
    
    renderer = ManimSceneRenderer()
    return renderer.render(QuickScene(), output_path)


# ========== 阶段 2: ThreeDScene 深度集成 ==========

class ThreeDCameraController:
    """
    3D 摄像机控制器
    
    提供 ThreeDScene 中的高级摄像机控制功能
    """
    
    def __init__(self, adapter: ManimCameraAdapter):
        self.adapter = adapter
        self.scene: Optional[ThreeDScene] = None
        self.camera_path: List[Dict[str, Any]] = []
    
    def set_scene(self, scene: ThreeDScene):
        """设置 3D 场景"""
        if not MANIM_AVAILABLE:
            return self
        
        self.scene = scene
        self.adapter.set_scene(scene)
        return self
    
    def orbit_camera(self, 
                     center: np.ndarray = None,
                     radius: float = 5.0,
                     phi: float = 60,
                     theta: float = 45,
                     duration: float = 3.0) -> 'ThreeDCameraController':
        """
        轨道摄像机控制
        
        Args:
            center: 轨道中心点
            radius: 轨道半径
            phi: 垂直角度 (度)
            theta: 水平角度 (度)
            duration: 动画时长
        """
        if not MANIM_AVAILABLE or self.scene is None:
            return self
        
        if center is None:
            center = np.array([0, 0, 0])
        
        # 设置 3D 场景摄像机方向
        self.scene.set_camera_orientation(
            phi=phi * np.pi / 180,
            theta=theta * np.pi / 180,
            frame_center=center
        )
        
        # 记录路径关键点
        self.camera_path.append({
            'type': 'orbit',
            'center': center,
            'radius': radius,
            'phi': phi,
            'theta': theta,
            'duration': duration
        })
        
        return self
    
    def move_camera_along_path(self, 
                                path_points: List[np.ndarray],
                                duration: float = 5.0,
                                rate_func=None) -> 'ThreeDCameraController':
        """
        沿路径移动摄像机
        
        Args:
            path_points: 路径点列表
            duration: 总时长
            rate_func: 速率函数 (缓动)
        """
        if not MANIM_AVAILABLE or self.scene is None:
            return self
        
        # 记录路径
        self.camera_path.append({
            'type': 'path',
            'points': path_points,
            'duration': duration,
            'rate_func': rate_func
        })
        
        # TODO: 实现路径动画
        print(f"  路径动画：{len(path_points)} 个点，{duration}秒")
        
        return self
    
    def auto_focus(self, 
                   mobject: Mobject,
                   zoom_factor: float = 1.5,
                   duration: float = 2.0) -> 'ThreeDCameraController':
        """
        自动聚焦到对象
        
        Args:
            mobject: 目标对象
            zoom_factor: 缩放因子
            duration: 动画时长
        """
        if not MANIM_AVAILABLE or self.scene is None:
            return self
        
        # 获取对象中心
        center = mobject.get_center()
        
        # 移动摄像机到对象
        self.scene.move_camera(center)
        
        # 调整缩放
        frame_width = self.scene.camera.frame_width / zoom_factor
        self.scene.camera.frame.set_width(frame_width)
        
        # 记录
        self.camera_path.append({
            'type': 'focus',
            'target': center,
            'zoom': zoom_factor,
            'duration': duration
        })
        
        return self
    
    def multi_camera_switch(self, 
                            camera_positions: List[Dict[str, Any]],
                            transition_duration: float = 1.0) -> 'ThreeDCameraController':
        """
        多摄像机切换
        
        Args:
            camera_positions: 摄像机位置列表
            transition_duration: 切换过渡时长
        """
        if not MANIM_AVAILABLE or self.scene is None:
            return self
        
        for i, pos in enumerate(camera_positions):
            self.camera_path.append({
                'type': 'switch',
                'index': i,
                'position': pos.get('position', [0, 0, 0]),
                'angle': pos.get('angle', 0),
                'duration': transition_duration
            })
        
        print(f"  ✓ 多摄像机切换：{len(camera_positions)} 个机位")
        
        return self
    
    def play_camera_animation(self, 
                              animation_type: str = 'orbit',
                              duration: float = 3.0) -> 'ThreeDCameraController':
        """
        播放摄像机动画
        
        Args:
            animation_type: 动画类型 ('orbit', 'path', 'switch')
            duration: 动画时长
        """
        if not MANIM_AVAILABLE or self.scene is None:
            return self
        
        from manim import Wait
        
        # 根据路径类型播放动画
        for waypoint in self.camera_path:
            if waypoint['type'] == 'orbit':
                # 轨道动画
                phi = waypoint.get('phi', 60)
                theta = waypoint.get('theta', 45)
                
                self.scene.set_camera_orientation(
                    phi=phi * np.pi / 180,
                    theta=theta * np.pi / 180,
                    run_time=duration
                )
                
            elif waypoint['type'] == 'path':
                # 路径动画
                points = waypoint.get('points', [])
                if len(points) > 0:
                    # 移动到路径起点
                    self.scene.camera.frame.move_to(points[0])
                    
                    # 沿路径移动 (简化实现)
                    for point in points[1:]:
                        self.scene.camera.frame.move_to(point)
                        self.scene.wait(duration / len(points))
                        
            elif waypoint['type'] == 'switch':
                # 机位切换
                position = waypoint.get('position', [0, 0, 0])
                self.scene.camera.frame.move_to(position)
                self.scene.wait(waypoint.get('duration', transition_duration))
        
        return self
    
    def export_camera_path(self, output_path: str = "camera_path.json") -> str:
        """
        导出摄像机路径到 JSON 文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        import json
        
        # 转换 numpy 数组为列表
        export_data = []
        for waypoint in self.camera_path:
            export_waypoint = waypoint.copy()
            if 'points' in export_waypoint:
                export_waypoint['points'] = [p.tolist() if hasattr(p, 'tolist') else p 
                                             for p in export_waypoint['points']]
            if 'center' in export_waypoint:
                c = export_waypoint['center']
                export_waypoint['center'] = c.tolist() if hasattr(c, 'tolist') else c
            if 'position' in export_waypoint:
                p = export_waypoint['position']
                export_waypoint['position'] = p.tolist() if hasattr(p, 'tolist') else p
            export_data.append(export_waypoint)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'camera_path': export_data,
                'total_waypoints': len(export_data)
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ 摄像机路径已导出：{output_path}")
        return output_path
    
    def get_camera_path(self) -> List[Dict[str, Any]]:
        """获取摄像机路径"""
        return self.camera_path
    
    def clear_path(self) -> 'ThreeDCameraController':
        """清除路径"""
        self.camera_path = []
        return self


# ========== 阶段 2: 性能基准测试 ==========

class ManimBenchmark:
    """
    Manim 性能基准测试工具
    """
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
    
    def test_render_time(self, 
                         scene_class: type = None,
                         duration: float = 10.0,
                         quality: str = "high") -> Dict[str, float]:
        """
        测试渲染时间
        
        Args:
            scene_class: 场景类
            duration: 视频时长
            quality: 渲染质量
        """
        import time
        
        if not MANIM_AVAILABLE:
            return {'error': 'Manim not installed'}
        
        if scene_class is None:
            # 创建简单测试场景
            class TestScene(Scene):
                def construct(self):
                    circle = Circle()
                    self.play(Create(circle))
                    self.wait(duration - 1)
                    self.play(FadeOut(circle))
            
            scene_class = TestScene
        
        # 测试渲染
        start_time = time.time()
        
        try:
            renderer = ManimSceneRenderer()
            output = renderer.render(scene_class(), "benchmark_test.mp4")
            render_time = time.time() - start_time
            
            self.results['render_time'] = render_time
            self.results['duration'] = duration
            self.results['fps'] = duration / render_time if render_time > 0 else 0
            
            return self.results
            
        except Exception as e:
            self.results['error'] = str(e)
            return self.results
    
    def test_memory_usage(self, 
                          num_objects: int = 100) -> Dict[str, Any]:
        """
        测试内存使用
        
        Args:
            num_objects: 对象数量
        """
        try:
            import psutil
        except ImportError:
            return {'error': 'psutil not installed (pip install psutil)'}
        
        import os
        
        if not MANIM_AVAILABLE:
            return {'error': 'Manim not installed'}
        
        process = psutil.Process(os.getpid())
        
        # 基准内存
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建对象
        adapter = ManimCameraAdapter()
        
        for i in range(num_objects):
            adapter.create_shape('circle', radius=0.1)
        
        # 峰值内存
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        self.results['baseline_memory_mb'] = baseline_memory
        self.results['peak_memory_mb'] = peak_memory
        self.results['memory_per_object_kb'] = (peak_memory - baseline_memory) / num_objects * 1024
        
        return self.results
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """运行完整基准测试"""
        print("\n" + "="*60)
        print("Manim 性能基准测试")
        print("="*60)
        
        if not MANIM_AVAILABLE:
            print("⏸️ Manim 未安装")
            return {'error': 'Manim not installed'}
        
        # 渲染时间测试
        print("\n1. 渲染时间测试...")
        render_result = self.test_render_time(duration=5.0)
        if 'error' not in render_result:
            print(f"   ✓ 渲染时间：{render_result['render_time']:.2f}秒")
            print(f"   ✓ 实时 FPS: {render_result['fps']:.2f}")
        else:
            error_msg = render_result['error']
            if 'ffmpeg' in error_msg.lower() or 'WinError' in error_msg:
                print(f"   ⚠️ 需要 FFmpeg (渲染引擎依赖)")
            else:
                print(f"   ⚠️ {error_msg}")
        
        # 内存测试
        print("\n2. 内存使用测试...")
        memory_result = self.test_memory_usage(num_objects=50)
        if 'error' not in memory_result:
            print(f"   ✓ 基准内存：{memory_result['baseline_memory_mb']:.2f} MB")
            print(f"   ✓ 峰值内存：{memory_result['peak_memory_mb']:.2f} MB")
            print(f"   ✓ 每对象内存：{memory_result['memory_per_object_kb']:.2f} KB")
        else:
            error_msg = memory_result['error']
            if 'psutil' in error_msg.lower():
                print(f"   ⏸️ 跳过 (安装 psutil: pip install psutil)")
            else:
                print(f"   ⚠️ {error_msg}")
        
        print("\n" + "="*60)
        print("基准测试完成")
        print("="*60)
        
        return self.results


if __name__ == "__main__":
    # 测试代码
    print("Testing ManimCameraAdapter...")
    
    if not MANIM_AVAILABLE:
        print("\nManim not installed. Running in simulation mode.")
        print("\nTo install Manim:")
        print("  pip install manim")
        print("\nNote: Manim requires FFmpeg and LaTeX for full functionality")
    else:
        print("\n✓ Manim is available")
        
        # 测试适配器
        adapter = ManimCameraAdapter()
        print(f"✓ Adapter created with config: {adapter.config.quality}")
        
        # 测试渲染器
        renderer = ManimSceneRenderer()
        print(f"✓ Renderer created")
        
        # 测试 3D 控制器
        controller = ThreeDCameraController(adapter)
        print(f"✓ 3D Camera Controller created")
        
        # 运行基准测试
        benchmark = ManimBenchmark()
        benchmark.run_full_benchmark()
        
        # 尝试快速演示
        try:
            print("\nRendering demo scene...")
            output = renderer.quick_demo()
            print(f"✓ Demo rendered to: {output}")
        except Exception as e:
            print(f"Demo render: {e}")
    
    print("\nManim adapter module test complete!")

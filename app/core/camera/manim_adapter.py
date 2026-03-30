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
        
        # 尝试快速演示
        try:
            print("\nRendering demo scene...")
            output = renderer.quick_demo()
            print(f"✓ Demo rendered to: {output}")
        except Exception as e:
            print(f"Demo render: {e}")
    
    print("\nManim adapter module test complete!")

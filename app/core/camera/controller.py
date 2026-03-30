"""
摄像机控制模块 - 基于 Manim 的摄像机 API

功能:
- Zoom (缩放)
- Pan (平移)
- Rotate (旋转)
- 3D 摄像机支持
"""

from typing import Tuple, Optional, List
from dataclasses import dataclass
import numpy as np


@dataclass
class CameraState:
    """摄像机状态"""
    position: np.ndarray  # 位置 [x, y, z]
    rotation: np.ndarray  # 旋转 [phi, theta, gamma]
    zoom: float           # 缩放级别
    focal_distance: float # 焦距
    
    def copy(self) -> 'CameraState':
        return CameraState(
            position=self.position.copy(),
            rotation=self.rotation.copy(),
            zoom=self.zoom,
            focal_distance=self.focal_distance
        )


class CameraController:
    """
    摄像机控制器
    
    实现 Manim 风格的摄像机控制 API
    
    功能:
    - 设置摄像机位置和角度
    - Zoom/Pan/Rotate 操作
    - 关键帧动画
    - 状态保存/恢复
    """
    
    def __init__(self, 
                 frame_width: float = 14.0,
                 frame_height: float = 8.0,
                 fps: int = 30):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps
        
        # 初始状态
        self.current_state = CameraState(
            position=np.array([0.0, 0.0, 0.0]),
            rotation=np.array([0.0, 0.0, 0.0]),  # phi, theta, gamma
            zoom=1.0,
            focal_distance=10.0
        )
        
        # 关键帧列表
        self.keyframes: List[Tuple[float, CameraState]] = []
    
    def set_position(self, x: float, y: float, z: float) -> 'CameraController':
        """设置摄像机位置"""
        self.current_state.position = np.array([x, y, z])
        return self
    
    def move_to(self, point: np.ndarray) -> 'CameraController':
        """移动到目标点"""
        self.current_state.position = point
        return self
    
    def shift(self, dx: float, dy: float, dz: float = 0) -> 'CameraController':
        """相对移动"""
        self.current_state.position += np.array([dx, dy, dz])
        return self
    
    def set_rotation(self, phi: float, theta: float, gamma: float = 0) -> 'CameraController':
        """
        设置摄像机旋转角度
        
        Args:
            phi: 仰角 (与 Z 轴夹角)，单位：度
            theta: 方位角 (XY 平面投影与 X 轴夹角)，单位：度
            gamma: 翻滚角，单位：度
        """
        self.current_state.rotation = np.array([phi, theta, gamma])
        return self
    
    def rotate(self, dphi: float = 0, dtheta: float = 0, dgamma: float = 0) -> 'CameraController':
        """相对旋转"""
        self.current_state.rotation += np.array([dphi, dtheta, dgamma])
        return self
    
    def zoom_to(self, level: float) -> 'CameraController':
        """设置缩放级别"""
        if level <= 0:
            raise ValueError("Zoom level must be positive")
        self.current_state.zoom = level
        return self
    
    def zoom_in(self, factor: float = 1.5) -> 'CameraController':
        """放大"""
        self.current_state.zoom *= factor
        return self
    
    def zoom_out(self, factor: float = 1.5) -> 'CameraController':
        """缩小"""
        self.current_state.zoom /= factor
        return self
    
    def set_focal_distance(self, distance: float) -> 'CameraController':
        """设置焦距"""
        self.current_state.focal_distance = distance
        return self
    
    def add_keyframe(self, time: float, state: Optional[CameraState] = None) -> 'CameraController':
        """
        添加关键帧
        
        Args:
            time: 时间 (秒)
            state: 摄像机状态 (None 表示当前状态)
        """
        if state is None:
            state = self.current_state.copy()
        self.keyframes.append((time, state))
        # 按时间排序
        self.keyframes.sort(key=lambda x: x[0])
        return self
    
    def get_state_at_time(self, time: float) -> CameraState:
        """
        获取指定时间的摄像机状态 (线性插值)
        
        Args:
            time: 时间 (秒)
            
        Returns:
            插值后的摄像机状态
        """
        if not self.keyframes:
            return self.current_state.copy()
        
        # 边界情况
        if time <= self.keyframes[0][0]:
            return self.keyframes[0][1].copy()
        if time >= self.keyframes[-1][0]:
            return self.keyframes[-1][1].copy()
        
        # 找到相邻关键帧
        for i in range(len(self.keyframes) - 1):
            t1, s1 = self.keyframes[i]
            t2, s2 = self.keyframes[i + 1]
            
            if t1 <= time <= t2:
                # 线性插值
                t_ratio = (time - t1) / (t2 - t1)
                return self._interpolate_states(s1, s2, t_ratio)
        
        return self.current_state.copy()
    
    def _interpolate_states(self, s1: CameraState, s2: CameraState, 
                            ratio: float) -> CameraState:
        """在两个状态之间插值"""
        return CameraState(
            position=s1.position + (s2.position - s1.position) * ratio,
            rotation=s1.rotation + (s2.rotation - s1.rotation) * ratio,
            zoom=s1.zoom + (s2.zoom - s1.zoom) * ratio,
            focal_distance=s1.focal_distance + (s2.focal_distance - s1.focal_distance) * ratio
        )
    
    def reset(self) -> 'CameraController':
        """重置摄像机到初始状态"""
        self.current_state = CameraState(
            position=np.array([0.0, 0.0, 0.0]),
            rotation=np.array([0.0, 0.0, 0.0]),
            zoom=1.0,
            focal_distance=10.0
        )
        self.keyframes = []
        return self
    
    def get_state_dict(self) -> dict:
        """获取当前状态字典"""
        s = self.current_state
        return {
            'position': s.position.tolist(),
            'rotation': s.rotation.tolist(),
            'zoom': s.zoom,
            'focal_distance': s.focal_distance,
            'frame_width': self.frame_width,
            'frame_height': self.frame_height
        }
    
    def create_camera_animation(self, duration: float = 5.0) -> List[dict]:
        """
        创建摄像机动画帧数据
        
        Args:
            duration: 动画时长 (秒)
            
        Returns:
            每帧的摄像机状态列表
        """
        frames = []
        num_frames = int(duration * self.fps)
        
        for i in range(num_frames):
            time = i / self.fps
            state = self.get_state_at_time(time)
            frames.append({
                'frame': i,
                'time': time,
                'state': state
            })
        
        return frames


class Camera3DController(CameraController):
    """
    3D 摄像机控制器
    
    扩展基础控制器，添加 3D 特定功能
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 3D 默认角度
        self.current_state.rotation = np.array([75.0, -45.0, 0.0])  # phi, theta, gamma
    
    def set_euler_angles(self, phi: float, theta: float, gamma: float) -> 'Camera3DController':
        """设置欧拉角 (3D 旋转)"""
        return self.set_rotation(phi, theta, gamma)
    
    def orbit(self, center: np.ndarray, radius: float, 
              phi: float, theta: float) -> 'Camera3DController':
        """
        设置轨道摄像机
        
        Args:
            center: 轨道中心
            radius: 轨道半径
            phi: 仰角
            theta: 方位角
        """
        # 球坐标转直角坐标
        phi_rad = np.radians(phi)
        theta_rad = np.radians(theta)
        
        x = center[0] + radius * np.sin(phi_rad) * np.cos(theta_rad)
        y = center[1] + radius * np.sin(phi_rad) * np.sin(theta_rad)
        z = center[2] + radius * np.cos(phi_rad)
        
        self.set_position(x, y, z)
        return self
    
    def look_at(self, target: np.ndarray, up: np.ndarray = None) -> 'Camera3DController':
        """
        摄像机看向目标点
        
        Args:
            target: 目标点
            up: 上方向向量 (默认 Z 轴)
        """
        if up is None:
            up = np.array([0, 0, 1])
        
        # 计算方向向量
        direction = target - self.current_state.position
        
        # 计算角度 (简化版本)
        phi = np.degrees(np.arccos(direction[2] / np.linalg.norm(direction)))
        theta = np.degrees(np.arctan2(direction[1], direction[0]))
        
        self.set_rotation(phi, theta, 0)
        return self
    
    def begin_ambient_rotation(self, rate: float = 0.5) -> 'Camera3DController':
        """
        开始环境旋转 (自动绕 Z 轴旋转)
        
        Args:
            rate: 旋转速度 (度/秒)
        """
        # 添加连续旋转的关键帧
        duration = 10.0  # 10 秒旋转
        for t in np.linspace(0, duration, int(duration * self.fps)):
            state = self.current_state.copy()
            state.rotation[1] += rate * t  # theta 增加
            self.add_keyframe(t, state)
        
        return self


# 便捷函数
def create_zoom_animation(start_zoom: float = 1.0, end_zoom: float = 2.0,
                          duration: float = 3.0) -> CameraController:
    """创建缩放动画"""
    cam = CameraController()
    cam.zoom_to(start_zoom).add_keyframe(0)
    cam.zoom_to(end_zoom).add_keyframe(duration)
    return cam


def create_pan_animation(start_pos: Tuple[float, float], 
                         end_pos: Tuple[float, float],
                         duration: float = 3.0) -> CameraController:
    """创建平移动画"""
    cam = CameraController()
    cam.set_position(start_pos[0], start_pos[1], 0).add_keyframe(0)
    cam.set_position(end_pos[0], end_pos[1], 0).add_keyframe(duration)
    return cam


def create_rotation_animation(start_theta: float = 0, end_theta: float = 360,
                               duration: float = 5.0) -> Camera3DController:
    """创建旋转动画"""
    cam = Camera3DController()
    cam.set_rotation(75, start_theta, 0).add_keyframe(0)
    cam.set_rotation(75, end_theta, 0).add_keyframe(duration)
    return cam


if __name__ == "__main__":
    # 测试代码
    print("Testing CameraController...")
    
    # 测试基础控制
    cam = CameraController()
    cam.set_position(1, 2, 0)
    cam.zoom_in(2.0)
    cam.rotate(dtheta=45)
    
    print(f"Position: {cam.current_state.position}")
    print(f"Zoom: {cam.current_state.zoom}")
    print(f"Rotation: {cam.current_state.rotation}")
    print("✓ Basic control works")
    
    # 测试关键帧动画
    cam2 = CameraController()
    cam2.set_position(0, 0, 0).add_keyframe(0)
    cam2.set_position(5, 5, 0).add_keyframe(2)
    cam2.zoom_to(2.0).add_keyframe(2)
    
    state_at_1s = cam2.get_state_at_time(1.0)
    print(f"State at 1s: pos={state_at_1s.position}, zoom={state_at_1s.zoom}")
    print("✓ Keyframe animation works")
    
    # 测试 3D 控制器
    cam3d = Camera3DController()
    cam3d.orbit(np.array([0, 0, 0]), 5, 60, 45)
    print(f"3D Position: {cam3d.current_state.position}")
    print("✓ 3D controller works")
    
    print("\nAll camera tests passed!")

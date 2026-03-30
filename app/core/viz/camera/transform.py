"""
摄像机系统 — 支持缩放、平移、旋转等摄像机运动

用于创建电影级的数据可视化镜头语言。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MotionType(str, Enum):
    """摄像机运动类型"""

    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    PAN_UP = "pan_up"
    PAN_DOWN = "pan_down"
    ROTATE_CW = "rotate_cw"
    ROTATE_CCW = "rotate_ccw"
    CUSTOM = "custom"


@dataclass
class CameraState:
    """摄像机状态"""

    x: float = 0.0  # 平移 X（归一化坐标 -1 到 1）
    y: float = 0.0  # 平移 Y（归一化坐标 -1 到 1）
    zoom: float = 1.0  # 缩放倍数
    rotation: float = 0.0  # 旋转角度（度）
    focus_x: float | None = None  # 焦点 X
    focus_y: float | None = None  # 焦点 Y

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "zoom": self.zoom,
            "rotation": self.rotation,
            "focus_x": self.focus_x or 0.0,
            "focus_y": self.focus_y or 0.0,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CameraState":
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            zoom=data.get("zoom", 1.0),
            rotation=data.get("rotation", 0.0),
            focus_x=data.get("focus_x"),
            focus_y=data.get("focus_y"),
        )


@dataclass
class Keyframe:
    """关键帧"""

    frame_index: int
    state: CameraState
    easing: str = "ease_in_out_cubic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame": self.frame_index,
            "state": self.state.to_dict(),
            "easing": self.easing,
        }


class Camera:
    """
    摄像机控制器

    支持关键帧动画和程序化运动。

    使用示例:
        camera = Camera(width=1920, height=1080)

        # 定义关键帧
        camera.add_keyframe(0, CameraState(zoom=1.0))
        camera.add_keyframe(30, CameraState(zoom=1.5, x=0.3))
        camera.add_keyframe(60, CameraState(zoom=1.0))

        # 获取指定帧的摄像机状态
        for frame in range(60):
            state = camera.get_state_at_frame(frame)
            apply_transform(state)
    """

    def __init__(self, width: float = 1920, height: float = 1080):
        self.width = width
        self.height = height
        self.default_state = CameraState()
        self.keyframes: list[Keyframe] = []
        self._motion_presets: dict[str, list[Keyframe]] = {}

        # 注册预设运动
        self._register_motion_presets()

    def add_keyframe(self, frame: int, state: CameraState, easing: str = "ease_in_out_cubic"):
        """添加关键帧"""
        keyframe = Keyframe(frame_index=frame, state=state, easing=easing)
        self.keyframes.append(keyframe)
        self.keyframes.sort(key=lambda k: k.frame_index)

    def clear_keyframes(self):
        """清除所有关键帧"""
        self.keyframes = []

    def get_state_at_frame(self, frame: int) -> CameraState:
        """获取指定帧的摄像机状态"""
        if not self.keyframes:
            return self.default_state

        # 找到前后关键帧
        before = None
        after = None

        for kf in self.keyframes:
            if kf.frame_index <= frame:
                before = kf
            if kf.frame_index > frame and after is None:
                after = kf
                break

        # 边界情况处理
        if before is None:
            return after.state
        if after is None:
            return before.state

        # 插值计算
        duration = after.frame_index - before.frame_index
        if duration == 0:
            return before.state

        t = (frame - before.frame_index) / duration
        t = self._apply_easing(t, before.easing)

        return self._interpolate(before.state, after.state, t)

    def _apply_easing(self, t: float, easing: str) -> float:
        """应用缓动函数"""
        if easing == "linear":
            return t
        elif easing == "ease_in_out_cubic":
            if t < 0.5:
                return 4 * t * t * t
            return 1 - pow(-2 * t + 2, 3) / 2
        elif easing == "ease_in_quad":
            return t * t
        elif easing == "ease_out_quad":
            return 1 - (1 - t) * (1 - t)
        elif easing == "ease_in_out_quad":
            if t < 0.5:
                return 2 * t * t
            return 1 - pow(-2 * t + 2, 2) / 2
        elif easing == "ease_out_bounce":
            if t < 1 / 2.75:
                return 7.5625 * t * t
            elif t < 2 / 2.75:
                t -= 1.5 / 2.75
                return 7.5625 * t * t + 0.75
            elif t < 2.5 / 2.75:
                t -= 2.25 / 2.75
                return 7.5625 * t * t + 0.9375
            else:
                t -= 2.625 / 2.75
                return 7.5625 * t * t + 0.984375
        else:
            return t

    def _interpolate(self, start: CameraState, end: CameraState, t: float) -> CameraState:
        """插值计算摄像机状态"""
        return CameraState(
            x=start.x + (end.x - start.x) * t,
            y=start.y + (end.y - start.y) * t,
            zoom=start.zoom + (end.zoom - start.zoom) * t,
            rotation=start.rotation + (end.rotation - start.rotation) * t,
            focus_x=self._lerp_optional(start.focus_x, end.focus_x, t),
            focus_y=self._lerp_optional(start.focus_y, end.focus_y, t),
        )

    def _lerp_optional(self, a: float | None, b: float | None, t: float) -> float | None:
        """可选值插值"""
        if a is None and b is None:
            return None
        if a is None:
            return b
        if b is None:
            return a
        return a + (b - a) * t

    def _register_motion_presets(self):
        """注册预设运动"""
        # 放大聚焦
        self._motion_presets["zoom_in_focus"] = [
            Keyframe(0, CameraState(zoom=1.0)),
            Keyframe(30, CameraState(zoom=2.0, x=0.2, y=0.1)),
        ]

        # 平移扫描
        self._motion_presets["pan_scan"] = [
            Keyframe(0, CameraState(x=-0.3)),
            Keyframe(30, CameraState(x=0.3)),
        ]

        # 缩放展示
        self._motion_presets["zoom_show"] = [
            Keyframe(0, CameraState(zoom=1.5)),
            Keyframe(20, CameraState(zoom=1.0)),
        ]

        # 旋转展示（用于饼图等）
        self._motion_presets["rotate_reveal"] = [
            Keyframe(0, CameraState(rotation=0)),
            Keyframe(60, CameraState(rotation=15)),
        ]

    def use_preset(self, preset_name: str, start_frame: int = 0, duration: int = 60):
        """使用预设运动"""
        if preset_name not in self._motion_presets:
            available = ", ".join(self._motion_presets.keys())
            raise ValueError(f"Unknown motion preset: {preset_name}. Available: {available}")

        preset = self._motion_presets[preset_name]

        # 缩放时间
        original_duration = preset[-1].frame_index - preset[0].frame_index
        time_scale = duration / original_duration if original_duration > 0 else 1.0

        for kf in preset:
            new_frame = start_frame + int(kf.frame_index * time_scale)
            self.add_keyframe(new_frame, kf.state, kf.easing)

    def apply_to_axes(self, ax, frame: int):
        """
        将摄像机变换应用到 matplotlib axes

        Args:
            ax: matplotlib axes 对象
            frame: 当前帧索引
        """
        state = self.get_state_at_frame(frame)

        # 保存原始限制
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]

        # 应用缩放
        if state.zoom != 1.0:
            x_range /= state.zoom
            y_range /= state.zoom

        # 计算中心点
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2

        # 应用平移
        x_center += state.x * x_range
        y_center += state.y * y_range

        # 设置新限制
        ax.set_xlim(x_center - x_range / 2, x_center + x_range / 2)
        ax.set_ylim(y_center - y_range / 2, y_center + y_range / 2)

        # 应用旋转（如果有）
        if state.rotation != 0:
            ax.set_rotation(state.rotation)

    def get_transform_matrix(self, frame: int) -> list[list[float]]:
        """
        获取变换矩阵（用于自定义渲染器）

        Returns:
            4x4 变换矩阵
        """
        state = self.get_state_at_frame(frame)

        import numpy as np

        # 平移矩阵
        T = np.array(
            [
                [1, 0, state.x],
                [0, 1, state.y],
                [0, 0, 1],
            ]
        )

        # 缩放矩阵
        S = np.array(
            [
                [state.zoom, 0, 0],
                [0, state.zoom, 0],
                [0, 0, 1],
            ]
        )

        # 旋转矩阵
        theta = np.radians(state.rotation)
        R = np.array(
            [
                [np.cos(theta), -np.sin(theta), 0],
                [np.sin(theta), np.cos(theta), 0],
                [0, 0, 1],
            ]
        )

        # 组合变换：先缩放，再旋转，最后平移
        M = T @ R @ S

        return M.tolist()

    def create_focus_motion(
        self,
        focus_point: tuple[float, float],
        zoom_level: float = 2.0,
        start_frame: int = 0,
        duration: int = 30,
    ):
        """
        创建聚焦运动

        Args:
            focus_point: 焦点坐标 (x, y)，归一化坐标 (-1 到 1)
            zoom_level: 缩放级别
            start_frame: 起始帧
            duration: 持续时间（帧数）
        """
        self.add_keyframe(start_frame, CameraState(zoom=1.0))
        self.add_keyframe(
            start_frame + duration,
            CameraState(
                zoom=zoom_level,
                x=focus_point[0],
                y=focus_point[1],
            ),
        )

    def create_reveal_motion(
        self,
        start_frame: int = 0,
        duration: int = 20,
    ):
        """
        创建揭示运动（从放大到正常）

        Args:
            start_frame: 起始帧
            duration: 持续时间（帧数）
        """
        self.add_keyframe(start_frame, CameraState(zoom=1.5))
        self.add_keyframe(start_frame + duration, CameraState(zoom=1.0))

    def to_dict(self) -> dict[str, Any]:
        """导出为字典"""
        return {
            "width": self.width,
            "height": self.height,
            "default_state": self.default_state.to_dict(),
            "keyframes": [kf.to_dict() for kf in self.keyframes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Camera":
        """从字典导入"""
        camera = cls(width=data.get("width", 1920), height=data.get("height", 1080))

        default_state = data.get("default_state")
        if default_state:
            camera.default_state = CameraState.from_dict(default_state)

        keyframes_data = data.get("keyframes", [])
        for kf_data in keyframes_data:
            camera.add_keyframe(
                kf_data["frame"],
                CameraState.from_dict(kf_data["state"]),
                kf_data.get("easing", "ease_in_out_cubic"),
            )

        return camera


# 使用示例
if __name__ == "__main__":
    # 创建摄像机
    camera = Camera(width=1920, height=1080)

    # 示例 1: 手动定义关键帧
    camera.add_keyframe(0, CameraState(zoom=1.0, x=0, y=0))
    camera.add_keyframe(30, CameraState(zoom=1.5, x=0.2, y=0.1))
    camera.add_keyframe(60, CameraState(zoom=1.0, x=0, y=0))

    # 获取各帧状态
    print("手动关键帧动画:")
    for frame in [0, 15, 30, 45, 60]:
        state = camera.get_state_at_frame(frame)
        print(f"  Frame {frame}: zoom={state.zoom:.2f}, x={state.x:.2f}, y={state.y:.2f}")

    # 示例 2: 使用预设
    camera.clear_keyframes()
    camera.use_preset("zoom_in_focus", start_frame=0, duration=30)

    print("\n预设运动 (zoom_in_focus):")
    for frame in [0, 15, 30]:
        state = camera.get_state_at_frame(frame)
        print(f"  Frame {frame}: zoom={state.zoom:.2f}, x={state.x:.2f}")

    # 示例 3: 聚焦运动
    camera.clear_keyframes()
    camera.create_focus_motion(focus_point=(0.3, -0.2), zoom_level=2.5, start_frame=0, duration=40)

    print("\n聚焦运动:")
    for frame in [0, 20, 40]:
        state = camera.get_state_at_frame(frame)
        print(f"  Frame {frame}: zoom={state.zoom:.2f}, focus=({state.x:.2f}, {state.y:.2f})")

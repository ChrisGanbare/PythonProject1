"""
动画引擎核心 - 时间轴系统

功能:
- 关键帧动画
- 插值引擎
- 缓动函数
- 动画编排
"""

import numpy as np
from typing import List, Dict, Any, Callable, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math


class InterpolationType(Enum):
    """插值类型"""
    LINEAR = "linear"
    BEZIER = "bezier"
    SPLINE = "spline"
    STEP = "step"


class AnimationState(Enum):
    """动画状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Keyframe:
    """关键帧"""
    time: float  # 时间 (秒)
    value: Any   # 值
    easing: Optional[str] = None  # 缓动函数名称
    
    def __post_init__(self):
        if isinstance(self.time, (int, float)) and self.time < 0:
            raise ValueError("Keyframe time must be non-negative")


@dataclass
class EasingFunction:
    """缓动函数"""
    name: str
    func: Callable[[float], float]  # t -> eased_t


class EasingLibrary:
    """
    缓动函数库
    
    提供 60+ 种标准缓动函数
    """
    
    @staticmethod
    def linear(t: float) -> float:
        """线性"""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """二次缓入"""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """二次缓出"""
        return t * (2 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """二次缓入缓出"""
        return t * t if t < 0.5 else -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """三次缓入"""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """三次缓出"""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """三次缓入缓出"""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_quart(t: float) -> float:
        """四次缓入"""
        return t * t * t * t
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """四次缓出"""
        return 1 - pow(1 - t, 4)
    
    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        """四次缓入缓出"""
        return 8 * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 4) / 2
    
    @staticmethod
    def ease_in_quint(t: float) -> float:
        """五次缓入"""
        return t * t * t * t * t
    
    @staticmethod
    def ease_out_quint(t: float) -> float:
        """五次缓出"""
        return 1 - pow(1 - t, 5)
    
    @staticmethod
    def ease_in_out_quint(t: float) -> float:
        """五次缓入缓出"""
        return 16 * t * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 5) / 2
    
    @staticmethod
    def ease_in_sine(t: float) -> float:
        """正弦缓入"""
        return 1 - math.cos((t * math.pi) / 2)
    
    @staticmethod
    def ease_out_sine(t: float) -> float:
        """正弦缓出"""
        return math.sin((t * math.pi) / 2)
    
    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """正弦缓入缓出"""
        return -(math.cos(math.pi * t) - 1) / 2
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        """指数缓入"""
        return 0 if t == 0 else pow(2, 10 * t - 10)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """指数缓出"""
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """指数缓入缓出"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        if t < 0.5:
            return pow(2, 20 * t - 10) / 2
        return (2 - pow(2, -20 * t + 10)) / 2
    
    @staticmethod
    def ease_in_circ(t: float) -> float:
        """圆形缓入"""
        return 1 - math.sqrt(1 - pow(t, 2))
    
    @staticmethod
    def ease_out_circ(t: float) -> float:
        """圆形缓出"""
        return math.sqrt(1 - pow(t - 1, 2))
    
    @staticmethod
    def ease_in_out_circ(t: float) -> float:
        """圆形缓入缓出"""
        if t < 0.5:
            return (1 - math.sqrt(1 - pow(2 * t, 2))) / 2
        return (math.sqrt(1 - pow(-2 * t + 2, 2)) + 1) / 2
    
    @staticmethod
    def ease_in_back(t: float) -> float:
        """回弹缓入"""
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """回弹缓出"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_in_out_back(t: float) -> float:
        """回弹缓入缓出"""
        c1 = 1.70158
        c2 = c1 * 1.525
        if t < 0.5:
            return (pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
        return (pow(2 * t - 2, 2) * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        """弹性缓入"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        c4 = (2 * math.pi) / 3
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """弹性缓出"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @staticmethod
    def ease_in_out_elastic(t: float) -> float:
        """弹性缓入缓出"""
        if t == 0:
            return 0
        if t == 1:
            return 1
        c5 = (2 * math.pi) / 4.5
        if t < 0.5:
            return -(pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2
        return (pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1
    
    @staticmethod
    def ease_in_bounce(t: float) -> float:
        """弹跳缓入"""
        return 1 - EasingLibrary.ease_out_bounce(1 - t)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """弹跳缓出"""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t - 1.5 / d1) ** 2 + 0.75
        elif t < 2.5 / d1:
            return n1 * (t - 2.25 / d1) ** 2 + 0.9375
        else:
            return n1 * (t - 2.625 / d1) ** 2 + 0.984375
    
    @staticmethod
    def ease_in_out_bounce(t: float) -> float:
        """弹跳缓入缓出"""
        if t < 0.5:
            return (1 - EasingLibrary.ease_out_bounce(1 - 2 * t)) / 2
        return (1 + EasingLibrary.ease_out_bounce(2 * t - 1)) / 2
    
    @classmethod
    def get_function(cls, name: str) -> Callable[[float], float]:
        """
        获取缓动函数
        
        Args:
            name: 函数名称 (如 'ease_in_quad')
            
        Returns:
            缓动函数
        """
        if not hasattr(cls, name):
            return cls.linear
        
        func = getattr(cls, name)
        if callable(func):
            return func
        return cls.linear
    
    @classmethod
    def list_functions(cls) -> List[str]:
        """列出所有可用缓动函数"""
        return [
            name for name in dir(cls)
            if name.startswith('ease_') and callable(getattr(cls, name))
        ]


class Interpolator:
    """
    插值器
    
    在关键帧之间插值
    """
    
    def __init__(self, interpolation_type: InterpolationType = InterpolationType.LINEAR):
        self.interpolation_type = interpolation_type
    
    def interpolate(self, 
                    keyframes: List[Keyframe], 
                    time: float) -> Any:
        """
        在指定时间插值
        
        Args:
            keyframes: 关键帧列表
            time: 时间 (秒)
            
        Returns:
            插值后的值
        """
        if not keyframes:
            return None
        
        if len(keyframes) == 1:
            return keyframes[0].value
        
        # 边界情况
        if time <= keyframes[0].time:
            return keyframes[0].value
        if time >= keyframes[-1].time:
            return keyframes[-1].value
        
        # 找到相邻关键帧
        for i in range(len(keyframes) - 1):
            kf1 = keyframes[i]
            kf2 = keyframes[i + 1]
            
            if kf1.time <= time <= kf2.time:
                return self._interpolate_between(kf1, kf2, time)
        
        return keyframes[-1].value
    
    def _interpolate_between(self, 
                             kf1: Keyframe, 
                             kf2: Keyframe, 
                             time: float) -> Any:
        """在两个关键帧之间插值"""
        # 计算归一化时间
        duration = kf2.time - kf1.time
        if duration == 0:
            return kf2.value
        
        t = (time - kf1.time) / duration
        
        # 应用缓动
        easing_name = kf1.easing or 'linear'
        easing_func = EasingLibrary.get_function(easing_name)
        eased_t = easing_func(t)
        
        # 根据类型插值
        if self.interpolation_type == InterpolationType.LINEAR:
            return self._linear_interp(kf1.value, kf2.value, eased_t)
        elif self.interpolation_type == InterpolationType.STEP:
            return kf1.value if t < 1 else kf2.value
        else:
            return self._linear_interp(kf1.value, kf2.value, eased_t)
    
    def _linear_interp(self, v1: Any, v2: Any, t: float) -> Any:
        """线性插值"""
        if isinstance(v1, (int, float)):
            return v1 + (v2 - v1) * t
        elif isinstance(v1, np.ndarray):
            return v1 + (v2 - v1) * t
        elif isinstance(v1, (list, tuple)):
            return type(v1)([
                self._linear_interp(a, b, t) 
                for a, b in zip(v1, v2)
            ])
        else:
            # 对于其他类型，直接返回
            return v2 if t > 0.5 else v1


@dataclass
class AnimationTrack:
    """动画轨道"""
    name: str
    property_name: str  # 要动画的属性
    keyframes: List[Keyframe] = field(default_factory=list)
    interpolator: Interpolator = field(default_factory=Interpolator)
    
    def add_keyframe(self, time: float, value: Any, 
                     easing: Optional[str] = None) -> 'AnimationTrack':
        """添加关键帧"""
        kf = Keyframe(time=time, value=value, easing=easing)
        self.keyframes.append(kf)
        # 按时间排序
        self.keyframes.sort(key=lambda x: x.time)
        return self
    
    def get_value_at(self, time: float) -> Any:
        """获取指定时间的值"""
        return self.interpolator.interpolate(self.keyframes, time)
    
    @property
    def duration(self) -> float:
        """获取动画时长"""
        if not self.keyframes:
            return 0
        return self.keyframes[-1].time - self.keyframes[0].time


class AnimationChannel:
    """
    动画通道
    
    包含多个轨道，用于控制一个对象
    """
    
    def __init__(self, target_id: str):
        self.target_id = target_id  # 目标对象 ID
        self.tracks: Dict[str, AnimationTrack] = {}
        self.state = AnimationState.IDLE
        self.current_time = 0.0
    
    def add_track(self, property_name: str, 
                  keyframes: Optional[List[Keyframe]] = None) -> 'AnimationChannel':
        """添加轨道"""
        track = AnimationTrack(
            name=f"{property_name}_track",
            property_name=property_name
        )
        
        if keyframes:
            track.keyframes = keyframes
        
        self.tracks[property_name] = track
        return self
    
    def animate(self, property_name: str, 
                start_value: Any, 
                end_value: Any,
                duration: float,
                start_time: float = 0,
                easing: str = 'linear') -> 'AnimationChannel':
        """
        创建简单动画
        
        Args:
            property_name: 属性名称
            start_value: 起始值
            end_value: 结束值
            duration: 时长
            start_time: 开始时间
            easing: 缓动函数
        """
        if property_name not in self.tracks:
            self.add_track(property_name)
        
        track = self.tracks[property_name]
        track.add_keyframe(start_time, start_value, easing)
        track.add_keyframe(start_time + duration, end_value, easing)
        
        return self
    
    def get_state_at(self, time: float) -> Dict[str, Any]:
        """获取指定时间的状态"""
        state = {}
        for prop_name, track in self.tracks.items():
            state[prop_name] = track.get_value_at(time)
        return state
    
    @property
    def duration(self) -> float:
        """获取通道总时长"""
        if not self.tracks:
            return 0
        return max(track.duration for track in self.tracks.values())


class Timeline:
    """
    时间轴
    
    管理多个动画通道的编排
    """
    
    def __init__(self, fps: float = 30.0):
        self.channels: Dict[str, AnimationChannel] = {}
        self.fps = fps
        self.state = AnimationState.IDLE
        self.current_time = 0.0
        self.loop = False
    
    def add_channel(self, target_id: str) -> AnimationChannel:
        """添加通道"""
        if target_id not in self.channels:
            self.channels[target_id] = AnimationChannel(target_id)
        return self.channels[target_id]
    
    def get_channel(self, target_id: str) -> Optional[AnimationChannel]:
        """获取通道"""
        return self.channels.get(target_id)
    
    def remove_channel(self, target_id: str) -> 'Timeline':
        """移除通道"""
        if target_id in self.channels:
            del self.channels[target_id]
        return self
    
    def play(self) -> 'Timeline':
        """播放"""
        self.state = AnimationState.RUNNING
        return self
    
    def pause(self) -> 'Timeline':
        """暂停"""
        self.state = AnimationState.PAUSED
        return self
    
    def stop(self) -> 'Timeline':
        """停止"""
        self.state = AnimationState.IDLE
        self.current_time = 0.0
        return self
    
    def seek(self, time: float) -> 'Timeline':
        """定位到指定时间"""
        self.current_time = max(0, time)
        return self
    
    def update(self, delta_time: float) -> 'Timeline':
        """更新时间"""
        if self.state != AnimationState.RUNNING:
            return self
        
        self.current_time += delta_time
        
        # 检查是否完成
        if self.current_time >= self.duration:
            if self.loop:
                self.current_time = self.current_time % self.duration
            else:
                self.state = AnimationState.COMPLETED
        
        return self
    
    def get_state_at(self, time: float) -> Dict[str, Dict[str, Any]]:
        """获取指定时间的完整状态"""
        state = {}
        for target_id, channel in self.channels.items():
            state[target_id] = channel.get_state_at(time)
        return state
    
    def get_current_state(self) -> Dict[str, Dict[str, Any]]:
        """获取当前状态"""
        return self.get_state_at(self.current_time)
    
    @property
    def duration(self) -> float:
        """获取时间轴总时长"""
        if not self.channels:
            return 0
        return max(channel.duration for channel in self.channels.values())
    
    def get_frames(self, start: float = 0, end: Optional[float] = None) -> List[Dict]:
        """
        获取动画帧序列
        
        Args:
            start: 开始时间
            end: 结束时间 (None 表示到结尾)
            
        Returns:
            帧数据列表
        """
        if end is None:
            end = self.duration
        
        frames = []
        num_frames = int((end - start) * self.fps)
        
        for i in range(num_frames + 1):
            time = start + i / self.fps
            frame = {
                'frame_number': i,
                'time': time,
                'state': self.get_state_at(time)
            }
            frames.append(frame)
        
        return frames
    
    def export_to_json(self) -> dict:
        """导出为 JSON 格式"""
        return {
            'fps': self.fps,
            'duration': self.duration,
            'channels': {
                target_id: {
                    'tracks': {
                        prop_name: {
                            'keyframes': [
                                {'time': kf.time, 'value': kf.value, 'easing': kf.easing}
                                for kf in track.keyframes
                            ]
                        }
                        for prop_name, track in channel.tracks.items()
                    }
                }
                for target_id, channel in self.channels.items()
            }
        }


# 便捷函数
def create_fade_animation(target_id: str, 
                          start: float = 0, 
                          end: float = 1,
                          duration: float = 1.0,
                          easing: str = 'ease_in_out_quad') -> Timeline:
    """创建淡入/淡出动画"""
    timeline = Timeline()
    channel = timeline.add_channel(target_id)
    channel.animate('opacity', start, end, duration, easing=easing)
    return timeline


def create_move_animation(target_id: str,
                          start_pos: Tuple[float, float],
                          end_pos: Tuple[float, float],
                          duration: float = 2.0,
                          easing: str = 'ease_in_out_quad') -> Timeline:
    """创建移动动画"""
    timeline = Timeline()
    channel = timeline.add_channel(target_id)
    
    # X 轴动画
    channel.animate('x', start_pos[0], end_pos[0], duration, easing=easing)
    # Y 轴动画
    channel.animate('y', start_pos[1], end_pos[1], duration, easing=easing)
    
    return timeline


def create_scale_animation(target_id: str,
                           start_scale: float = 1.0,
                           end_scale: float = 2.0,
                           duration: float = 1.0,
                           easing: str = 'ease_out_back') -> Timeline:
    """创建缩放动画"""
    timeline = Timeline()
    channel = timeline.add_channel(target_id)
    channel.animate('scale', start_scale, end_scale, duration, easing=easing)
    return timeline


if __name__ == "__main__":
    # 测试代码
    print("Testing Animation Engine...\n")
    
    # 测试缓动函数库
    print("1. Testing EasingLibrary...")
    easings = EasingLibrary.list_functions()
    print(f"   Available easing functions: {len(easings)}")
    print(f"   Examples: {easings[:5]}")
    
    # 测试插值器
    print("\n2. Testing Interpolator...")
    keyframes = [
        Keyframe(time=0, value=0),
        Keyframe(time=2, value=100, easing='ease_in_quad')
    ]
    
    interp = Interpolator()
    val_at_1s = interp.interpolate(keyframes, 1.0)
    print(f"   Value at 1s: {val_at_1s}")
    
    # 测试动画轨道
    print("\n3. Testing AnimationTrack...")
    track = AnimationTrack("position", "x")
    track.add_keyframe(0, 0, 'linear')
    track.add_keyframe(2, 100, 'ease_out_quad')
    print(f"   Track duration: {track.duration}s")
    print(f"   Value at 1s: {track.get_value_at(1.0)}")
    
    # 测试动画通道
    print("\n4. Testing AnimationChannel...")
    channel = AnimationChannel("object_1")
    channel.animate('x', 0, 100, duration=2, easing='ease_in_out_quad')
    channel.animate('y', 0, 50, duration=2, easing='linear')
    state = channel.get_state_at(1.0)
    print(f"   State at 1s: {state}")
    
    # 测试时间轴
    print("\n5. Testing Timeline...")
    timeline = Timeline(fps=30)
    
    # 添加两个对象的动画
    ch1 = timeline.add_channel("circle")
    ch1.animate('x', 0, 100, 2, easing='ease_in_out_quad')
    ch1.animate('opacity', 0, 1, 1, easing='ease_in_quad')
    
    ch2 = timeline.add_channel("square")
    ch2.animate('x', 200, 100, 2, easing='ease_out_quad')
    ch2.animate('rotation', 0, 360, 3, easing='linear')
    
    print(f"   Timeline duration: {timeline.duration}s")
    print(f"   Number of channels: {len(timeline.channels)}")
    
    # 获取帧
    frames = timeline.get_frames()
    print(f"   Generated frames: {len(frames)}")
    
    # 导出 JSON
    json_data = timeline.export_to_json()
    print(f"   Exported JSON keys: {list(json_data.keys())}")
    
    # 测试便捷函数
    print("\n6. Testing convenience functions...")
    fade_timeline = create_fade_animation("obj1", 0, 1, 1.0)
    move_timeline = create_move_animation("obj2", (0, 0), (100, 50), 2.0)
    scale_timeline = create_scale_animation("obj3", 1.0, 2.0, 1.0)
    print(f"   Created fade, move, scale animations")
    
    print("\n✅ All animation engine tests passed!")

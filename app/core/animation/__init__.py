"""
Core Animation Module

动画引擎系统，支持关键帧、缓动、时间轴
"""

from .timeline import (
    Timeline,
    AnimationChannel,
    AnimationTrack,
    Keyframe,
    Interpolator,
    InterpolationType,
    AnimationState,
    EasingLibrary,
    create_fade_animation,
    create_move_animation,
    create_scale_animation
)

__version__ = "1.0.0"
__all__ = [
    'Timeline',
    'AnimationChannel',
    'AnimationTrack',
    'Keyframe',
    'Interpolator',
    'InterpolationType',
    'AnimationState',
    'EasingLibrary',
    'create_fade_animation',
    'create_move_animation',
    'create_scale_animation'
]

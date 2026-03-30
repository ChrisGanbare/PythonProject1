"""
Core Camera Module

摄像机控制系统，支持 2D/3D 和 Manim 集成
"""

from .controller import (
    CameraController,
    Camera3DController,
    CameraState,
    create_zoom_animation,
    create_pan_animation,
    create_rotation_animation
)

try:
    from .manim_adapter import (
        ManimCameraAdapter,
        ManimSceneRenderer,
        ManimConfig,
        MANIM_AVAILABLE
    )
except ImportError:
    pass

__version__ = "1.0.0"
__all__ = [
    'CameraController',
    'Camera3DController',
    'CameraState',
    'create_zoom_animation',
    'create_pan_animation',
    'create_rotation_animation',
    'ManimCameraAdapter',
    'ManimSceneRenderer',
    'ManimConfig'
]

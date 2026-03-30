"""
渲染引擎层 — Render Engine Layer
==================================
负责：代码脚本 → 帧图像 → 视频文件

子模块：
  visualization/ - 可视化后端：Matplotlib、Plotly、Manim backend 抽象
  media/         - 媒体处理：视频编辑、帧缓存、OpenCV 封装
  core/          - 质量控制：quality_gate、self_correction、task_manager
"""

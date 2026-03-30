"""
运维基础层 — Operations Infrastructure Layer
=============================================
负责：作业调度、Web API、配置管理、公共工具

子模块：
  studio/ - 作业生命周期：RenderJob DB、schedule/run/query
  webapp/ - Dashboard API：FastAPI 路由、lifespan、preflight
  config/ - 配置管理：Settings（Pydantic）、质量预设、环境变量
  utils/  - 公共工具：时间、验证器、帮助函数
"""

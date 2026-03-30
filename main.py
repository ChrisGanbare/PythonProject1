#!/usr/bin/env python
"""
PythonProject1 主入口启动程序

数据可视化视频生成平台 - v2.2

功能:
    - 启动 API 服务
    - 运行演示
    - CLI 工具入口

使用示例:
    ```bash
    # 仅输入 main.py：打印「下一步」操作提示
    python main.py

    # 启动 API 服务
    python main.py api

    # Web 控制台
    python main.py dashboard

    # 运行演示 / CLI / 帮助
    python main.py demo
    python main.py cli list-templates
    python main.py --help
    ```
"""

import argparse
import os
import sys
from pathlib import Path

# 将 app/ 及 app/projects/ 注入 sys.path，使得
# "from shared.xxx import" / "from api.xxx import" 等在整个进程中生效
_ROOT = Path(__file__).resolve().parent
_APP = _ROOT / "app"
for _p in (_APP, _APP / "projects"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)


def print_banner():
    """打印欢迎横幅（执行子命令前）"""
    print("=" * 70)
    print(" PythonProject1 - 数据可视化视频生成平台 v2.3.0")
    print("=" * 70)
    print()


def print_next_steps() -> None:
    """仅执行 python main.py 时：提示下一步可执行的操作。"""
    print("未指定子命令。你可以按场景选择下一步：")
    print()
    print("  【常用】")
    print("    python main.py dashboard     启动 Web 控制台（默认 http://127.0.0.1:8090）")
    print("    python main.py dashboard --host 0.0.0.0 --port 8090   局域网/服务器监听")
    print("    python main.py api           启动统一 HTTP 服务（默认端口 8000，与控制台同源应用）")
    print()
    print("  【其他】")
    print("    python main.py demo          交互式选择并运行演示脚本")
    print("    python main.py doctor        上线前自检（FFmpeg、依赖、库目录、首页）")
    print("    python main.py status        检查部分依赖是否已安装")
    print("    python main.py clean         清理缓存与部分临时文件（慎用）")
    print("    python main.py cli --help    命令行工具帮助")
    print()
    print("  【说明】")
    print("    python main.py --help        查看所有子命令与参数")
    print("    探活与健康：启动后访问 GET /api/studio/v1/health")
    print("    架构前缀清单：GET /api/meta/architecture")
    print("    业务落地（非技术说明）：docs/业务落地说明.md")
    print("    配置模板：复制 .env.example 为 .env")
    print()


def cmd_api(args):
    """启动 API 服务"""
    from api.main import main as api_main
    import sys
    
    # 构建 API 启动参数
    api_args = []
    if hasattr(args, 'port') and args.port:
        api_args.extend(['--port', str(args.port)])
    if hasattr(args, 'reload') and args.reload:
        api_args.append('--reload')
    if hasattr(args, 'host') and args.host:
        api_args.extend(['--host', args.host])
    
    # 设置 sys.argv 并调用
    sys.argv = ['api'] + api_args
    api_main()


def cmd_demo(args):
    """运行演示"""
    print("选择演示:")
    print("  1. 端到端演示 (demo_e2e.py)")
    print("  2. API 演示 (demo_api.py)")
    print("  3. v2.0 演示 (demo_v2.py)")
    print()
    
    choice = input("请输入选项 (1-3): ").strip()
    
    demos = {
        "1": "demo_e2e.py",
        "2": "demo_api.py",
        "3": "demo_v2.py"
    }
    
    demo_file = demos.get(choice, "demo_e2e.py")
    print(f"\n运行演示：{demo_file}")
    
    # 执行演示
    import subprocess
    subprocess.run([sys.executable, "demos/" + demo_file])


def cmd_dashboard(args):
    """启动 Dashboard 控制台"""
    if getattr(args, "host", None) is not None:
        os.environ["DASHBOARD_HOST"] = args.host
    if getattr(args, "port", None) is not None:
        os.environ["DASHBOARD_PORT"] = str(args.port)

    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = os.environ.get("DASHBOARD_PORT", "8090")
    print("启动 Dashboard 控制台...")
    print(f"访问地址：http://{host}:{port}")
    print()

    from scripts.dashboard import run_dashboard

    run_dashboard()


def cmd_cli(args):
    """CLI 工具"""
    from cli.video import main as cli_main
    
    # 传递 CLI 参数
    sys.argv = ['cli'] + args.cli_args
    cli_main()


def cmd_clean(args):
    """清理缓存和临时文件"""
    import shutil
    
    print("清理临时文件...")
    
    # 清理目录
    dirs_to_clean = [
        "__pycache__",
        "runtime/outputs",
        "runtime/temp",
        "runtime/cache"
    ]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  ✓ 清理：{dir_name}")
    
    # 清理临时文件
    files_to_clean = list(Path(".").glob("*.html")) + \
                     list(Path(".").glob("*.json")) + \
                     list(Path(".").glob("*.mp4"))
    
    for file_path in files_to_clean:
        if file_path.name not in ["e2e_demo_config.json"]:  # 保留重要文件
            file_path.unlink()
            print(f"  ✓ 清理：{file_path.name}")
    
    print("清理完成!")


def cmd_doctor(args):
    """环境自检（FFmpeg、关键依赖、Studio 库目录、静态页）。"""
    from shared.ops.webapp.preflight import print_report_and_exit

    return print_report_and_exit()


def cmd_status(args):
    """显示项目状态"""
    print("项目状态:")
    print()
    
    # 检查依赖
    print("依赖检查:")
    try:
        import plotly
        print(f"  ✓ plotly: {plotly.__version__}")
    except ImportError:
        print(f"  ✗ plotly: 未安装")
    
    try:
        import fastapi
        print(f"  ✓ fastapi: {fastapi.__version__}")
    except ImportError:
        print(f"  ✗ fastapi: 未安装")
    
    try:
        import manim
        print(f"  ✓ manim: 已安装")
    except ImportError:
        print(f"  ✗ manim: 未安装 (可选)")
    
    print()
    
    # 显示统计
    print("项目统计:")
    print(f"  模板数量：6 种")
    print(f"  品牌主题：6 个")
    print(f"  支持平台：6 个")
    print(f"  API 端点：8 个")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PythonProject1 主入口启动程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python main.py api              # 启动 API 服务
    python main.py demo             # 运行演示
    python main.py cli list-templates  # CLI 工具
    python main.py clean            # 清理缓存
    python main.py status           # 查看状态
    python main.py doctor           # 上线前自检
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # API 命令
    api_parser = subparsers.add_parser("api", help="启动统一 API（同源 Dashboard，无旧版 /api/v1/jobs）")
    api_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    api_parser.add_argument("--port", type=int, default=8000, help="端口号")
    api_parser.add_argument("--reload", action="store_true", help="热重载")
    api_parser.set_defaults(func=cmd_api)
    
    # Demo 命令
    demo_parser = subparsers.add_parser("demo", help="运行演示")
    demo_parser.set_defaults(func=cmd_demo)
    
    # CLI 命令
    cli_parser = subparsers.add_parser("cli", help="CLI 工具")
    cli_parser.add_argument("cli_args", nargs=argparse.REMAINDER, help="CLI 参数")
    cli_parser.set_defaults(func=cmd_cli)
    
    # Clean 命令
    clean_parser = subparsers.add_parser("clean", help="清理缓存和临时文件")
    clean_parser.set_defaults(func=cmd_clean)
    
    # Status 命令
    status_parser = subparsers.add_parser("status", help="显示项目状态")
    status_parser.set_defaults(func=cmd_status)

    # Doctor 命令（业务落地自检）
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="环境自检：FFmpeg、关键依赖、Studio 库目录、static 首页",
    )
    doctor_parser.set_defaults(func=cmd_doctor)
    
    # Dashboard 命令
    dashboard_parser = subparsers.add_parser("dashboard", help="启动 Dashboard 控制台")
    dashboard_parser.add_argument(
        "--host",
        default=None,
        help="监听地址（不设则沿用环境变量 DASHBOARD_HOST，默认 127.0.0.1；外网常用 0.0.0.0）",
    )
    dashboard_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="端口（不设则沿用 DASHBOARD_PORT，默认 8090）",
    )
    dashboard_parser.set_defaults(func=cmd_dashboard)
    
    # 解析参数
    args = parser.parse_args()

    if not args.command:
        print_next_steps()
        return 0

    # doctor 面向脚本/运维输出，不打印横幅便于解析
    if args.command != "doctor":
        print_banner()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

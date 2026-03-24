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
    # 启动 API 服务
    python start.py api
    
    # 运行演示
    python start.py demo
    
    # CLI 工具
    python start.py cli list-templates
    
    # 查看帮助
    python start.py --help
    ```
"""

import sys
import argparse
from pathlib import Path


def print_banner():
    """打印欢迎横幅"""
    print("="*70)
    print(" PythonProject1 - 数据可视化视频生成平台 v2.2")
    print("="*70)
    print()
    print("快速开始:")
    print("  python start.py api        - 启动 API 服务")
    print("  python start.py dashboard  - 启动 Web 控制台")
    print("  python start.py demo       - 运行演示")
    print("  python start.py --help     - 查看帮助")
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
    print("启动 Dashboard 控制台...")
    print("访问地址：http://localhost:8090")
    print()
    
    # 导入并运行 dashboard
    sys.path.insert(0, str(Path(__file__).parent))
    from scripts.dashboard import main as dashboard_main
    dashboard_main()


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
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="PythonProject1 主入口启动程序",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
    python start.py api              # 启动 API 服务
    python start.py demo             # 运行演示
    python start.py cli list-templates  # CLI 工具
    python start.py clean            # 清理缓存
    python start.py status           # 查看状态
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # API 命令
    api_parser = subparsers.add_parser("api", help="启动 API 服务")
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
    
    # Dashboard 命令
    dashboard_parser = subparsers.add_parser("dashboard", help="启动 Dashboard 控制台")
    dashboard_parser.set_defaults(func=cmd_dashboard)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

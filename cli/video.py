"""
命令行工具 - 视频生成 CLI

提供完整的命令行接口用于视频创作
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def cmd_create_video(args):
    """创建视频命令"""
    from core.templates import get_template
    from core.data.sources import InlineDataSource, CSVSource, ExcelSource
    from core.brand import get_theme
    from core.render import create_renderer
    
    # 1. 加载数据
    print(f"加载数据：{args.data}")
    if args.data.endswith(".csv"):
        data_source = CSVSource(args.data)
    elif args.data.endswith((".xlsx", ".xls")):
        data_source = ExcelSource(args.data)
    else:
        print("错误：仅支持 CSV 和 Excel 文件")
        return 1
    
    # 2. 选择模板
    print(f"选择模板：{args.template}")
    template = get_template(args.template)
    if not template:
        print(f"错误：未知模板 '{args.template}'")
        return 1
    
    # 3. 选择品牌
    print(f"选择品牌：{args.brand}")
    brand = get_theme(args.brand)
    if not brand:
        print(f"错误：未知品牌 '{args.brand}'")
        return 1
    
    # 4. 构建视频清单
    print("构建视频清单...")
    manifest = template.build(data_source, brand)
    
    # 5. 渲染视频
    print(f"渲染视频...")
    renderer = create_renderer(backend="plotly")
    output_path = renderer.render(manifest.to_dict(), args.output)
    
    print(f"✓ 视频已生成：{output_path}")
    return 0


def cmd_list_templates(args):
    """列出模板命令"""
    from core.templates import list_templates
    
    templates = list_templates()
    
    print(f"\n可用模板 ({len(templates)} 个):")
    print("-" * 50)
    for name in sorted(templates.keys()):
        print(f"  • {name}")
    
    return 0


def cmd_list_themes(args):
    """列出品牌主题命令"""
    from core.brand import list_themes
    
    themes = list_themes()
    
    print(f"\n可用品牌主题 ({len(themes)} 个):")
    print("-" * 50)
    for name, theme in sorted(themes.items()):
        print(f"  • {name}: {theme.description}")
    
    return 0


def cmd_demo(args):
    """运行演示命令"""
    from core.templates import get_template
    from core.data.sources import InlineDataSource
    from core.brand import get_theme
    from core.render import create_renderer
    
    # 示例数据
    data = {
        "date": ["2024-Q1", "2024-Q1", "2024-Q1",
                 "2024-Q2", "2024-Q2", "2024-Q2"],
        "category": ["产品 A", "产品 B", "产品 C",
                     "产品 A", "产品 B", "产品 C"],
        "value": [100, 150, 200, 130, 170, 220]
    }
    
    # 创建模板
    template = get_template("bar_chart_race")
    data_source = InlineDataSource(data)
    brand = get_theme("corporate")
    
    # 构建清单
    manifest = template.build(data_source, brand)
    
    # 渲染
    renderer = create_renderer()
    output_path = renderer.render(manifest.to_dict(), args.output or "demo_output.mp4")
    
    print(f"✓ 演示视频已生成：{output_path}")
    return 0


def create_parser() -> argparse.ArgumentParser:
    """创建 CLI 解析器"""
    parser = argparse.ArgumentParser(
        prog="pv",
        description="PythonProject1 视频生成 CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # create 命令
    create_parser = subparsers.add_parser(
        "create",
        help="创建视频"
    )
    create_parser.add_argument(
        "--data", "-d",
        required=True,
        help="数据文件路径 (CSV/Excel)"
    )
    create_parser.add_argument(
        "--template", "-t",
        default="bar_chart_race",
        help="模板名称"
    )
    create_parser.add_argument(
        "--brand", "-b",
        default="default",
        help="品牌主题"
    )
    create_parser.add_argument(
        "--output", "-o",
        default="output.mp4",
        help="输出文件路径"
    )
    create_parser.set_defaults(func=cmd_create_video)
    
    # list templates 命令
    list_tpl_parser = subparsers.add_parser(
        "list-templates",
        help="列出所有模板"
    )
    list_tpl_parser.set_defaults(func=cmd_list_templates)
    
    # list themes 命令
    list_theme_parser = subparsers.add_parser(
        "list-themes",
        help="列出所有品牌主题"
    )
    list_theme_parser.set_defaults(func=cmd_list_themes)
    
    # demo 命令
    demo_parser = subparsers.add_parser(
        "demo",
        help="运行演示"
    )
    demo_parser.add_argument(
        "--output", "-o",
        help="输出文件路径"
    )
    demo_parser.set_defaults(func=cmd_demo)
    
    return parser


def main(argv=None):
    """CLI 入口"""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

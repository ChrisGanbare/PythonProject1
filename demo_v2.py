"""
Flourish 对标演示 - v2.0 新架构展示

展示新的模板引擎、数据源、品牌系统
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def demo_templates():
    """演示模板系统"""
    print("\n" + "="*60)
    print("1. 模板系统演示")
    print("="*60)
    
    from core.templates import get_template, list_templates
    from core.templates.base import TemplateConfig
    
    # 列出所有模板
    templates = list_templates()
    print(f"\n可用模板：{len(templates)} 个")
    for name in templates.keys():
        print(f"  - {name}")
    
    # 创建柱状图竞赛模板
    config = TemplateConfig(
        name="Bar Chart Race Demo",
        width=1920,
        height=1080,
        animation_duration=2.0
    )
    
    template = get_template("bar_chart_race", config)
    print(f"\n✓ 创建模板：{template.config.name}")
    print(f"  类型：{template.config.chart_type}")
    print(f"  数据要求：{template.data_schema.required_columns}")
    
    return True


def demo_data_sources():
    """演示数据源系统"""
    print("\n" + "="*60)
    print("2. 数据源演示")
    print("="*60)
    
    from core.data.sources import (
        CSVSource,
        ExcelSource,
        InlineDataSource,
        load_data
    )
    
    # 内联数据源
    data = {
        "date": ["2024-01", "2024-01", "2024-01",
                 "2024-02", "2024-02", "2024-02"],
        "category": ["A", "B", "C", "A", "B", "C"],
        "value": [100, 150, 200, 120, 160, 210]
    }
    
    source = InlineDataSource(data)
    df = source.load()
    
    print(f"\n✓ 内联数据源")
    print(f"  行数：{len(df)}")
    print(f"  列：{list(df.columns)}")
    print(f"  数据预览:")
    print(df.head())
    
    # 数据验证
    from core.data.schema import DataSchema
    
    schema = DataSchema(
        required_columns=["date", "category", "value"]
    )
    
    is_valid, errors = schema.validate(df)
    print(f"\n✓ 数据验证：{'通过' if is_valid else '失败'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    return True


def demo_brand_system():
    """演示品牌系统"""
    print("\n" + "="*60)
    print("3. 品牌系统演示")
    print("="*60)
    
    from core.brand import (
        BrandStyle,
        ColorPalette,
        FontPair,
        list_themes,
        get_theme
    )
    
    # 列出所有主题
    themes = list_themes()
    print(f"\n可用品牌主题：{len(themes)} 个")
    for name in themes.keys():
        print(f"  - {name}")
    
    # 获取企业主题
    corporate = get_theme("corporate")
    print(f"\n✓ 企业风格")
    print(f"  主色：{corporate.colors.primary}")
    print(f"  次色：{corporate.colors.secondary}")
    print(f"  标题字体：{corporate.fonts.heading}")
    
    # 创建自定义品牌
    custom_brand = BrandStyle(
        name="Custom Brand",
        colors=ColorPalette(
            primary="#FF5733",
            secondary="#33FF57",
            accent="#3357FF"
        ),
        fonts=FontPair(
            heading="Arial Black",
            body="Arial",
            heading_size=56
        )
    )
    
    print(f"\n✓ 自定义品牌")
    print(f"  名称：{custom_brand.name}")
    print(f"  颜色数：{len(custom_brand.colors.to_dict())}")
    print(f"  字体配置：{custom_brand.fonts.heading}")
    
    return True


def demo_full_pipeline():
    """演示完整工作流"""
    print("\n" + "="*60)
    print("4. 完整工作流演示")
    print("="*60)
    
    from core.templates import get_template
    from core.templates.base import TemplateConfig
    from core.data.sources import InlineDataSource
    from core.brand import get_theme
    
    # 1. 准备数据
    print("\n步骤 1: 准备数据...")
    data = {
        "date": ["2024-Q1", "2024-Q1", "2024-Q1", "2024-Q1",
                 "2024-Q2", "2024-Q2", "2024-Q2", "2024-Q2"],
        "category": ["产品 A", "产品 B", "产品 C", "产品 D",
                     "产品 A", "产品 B", "产品 C", "产品 D"],
        "value": [100, 150, 200, 120,
                  130, 170, 220, 140]
    }
    source = InlineDataSource(data)
    print("  ✓ 数据加载完成")
    
    # 2. 选择模板
    print("\n步骤 2: 选择模板...")
    template = get_template("bar_chart_race")
    print(f"  ✓ 模板：bar_chart_race")
    
    # 3. 选择品牌
    print("\n步骤 3: 选择品牌...")
    brand = get_theme("corporate")
    print(f"  ✓ 品牌：{brand.name}")
    
    # 4. 构建视频清单
    print("\n步骤 4: 构建视频清单...")
    manifest = template.build(source, brand)
    
    print(f"  ✓ 视频清单生成")
    print(f"    模板：{manifest.template_name}")
    print(f"    数据哈希：{manifest.data_hash}")
    print(f"    场景数：{len(manifest.scenes)}")
    print(f"    转场数：{len(manifest.transitions)}")
    print(f"    品牌：{manifest.brand_style_name}")
    
    # 5. 导出配置
    print("\n步骤 5: 导出配置...")
    config_dict = manifest.to_dict()
    print(f"  ✓ 配置已导出为字典")
    print(f"    键：{list(config_dict.keys())}")
    
    print("\n✓ 完整工作流演示完成!")
    
    return True


def demo_chart_types():
    """演示图表类型"""
    print("\n" + "="*60)
    print("5. 图表类型演示")
    print("="*60)
    
    from core.templates import get_template
    from core.data.sources import InlineDataSource
    
    # 准备示例数据
    sample_data = {
        "category": ["A", "B", "C", "D", "E"],
        "value": [10, 25, 15, 30, 20]
    }
    source = InlineDataSource(sample_data)
    
    # 支持的图表类型
    chart_templates = [
        "bar_chart_race",
        "bar_chart_horizontal",
        "line_chart_animated",
        "scatter_plot_dynamic",
        "bubble_chart",
        "area_chart_stacked"
    ]
    
    print("\n支持的图表类型:")
    for template_name in chart_templates:
        try:
            template = get_template(template_name)
            print(f"  ✓ {template_name}")
        except Exception as e:
            print(f"  ✗ {template_name}: {e}")
    
    return True


def main():
    """主函数"""
    print("\n" + "#"*60)
    print("# PythonProject1 v2.0 - Flourish 对标演示")
    print("#"*60)
    
    try:
        # 运行所有演示
        demo_templates()
        demo_data_sources()
        demo_brand_system()
        demo_full_pipeline()
        demo_chart_types()
        
        print("\n" + "="*60)
        print("✅ 所有演示完成!")
        print("="*60)
        
        print("\n📊 v2.0 新能力:")
        print("  ✓ 模板系统：6+ 种图表模板")
        print("  ✓ 数据源：CSV/Excel/JSON/API/Inline")
        print("  ✓ 品牌系统：6 个预定义主题")
        print("  ✓ 完整工作流：数据 → 模板 → 品牌 → 清单")
        print("  ✓ 图表类型：柱状图/折线图/散点图/气泡图/面积图")
        
        print("\n🎯 对标 Flourish:")
        print("  ✓ 模板化创作")
        print("  ✓ 多数据源绑定")
        print("  ✓ 品牌定制")
        print("  ✓ 专业图表库")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

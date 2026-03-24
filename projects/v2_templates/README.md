# v2 Templates

v2.2 通用模板渲染器

## 支持的模板

- `bar_chart_race` - 柱状图竞赛
- `line_chart_animated` - 动态折线图
- `scatter_plot_dynamic` - 动态散点图
- `area_chart_stacked` - 堆叠面积图
- `bubble_chart` - 气泡图
- `bar_chart_horizontal` - 水平柱状图

## 使用方式

### AI 编译

```json
{
  "project": "v2_templates",
  "task": "render",
  "kwargs": {
    "template": "bar_chart_race",
    "data": {
      "date": ["2024-01", "2024-02"],
      "category": ["A", "B"],
      "value": [100, 200]
    },
    "brand": "corporate",
    "platform": "bilibili"
  }
}
```

### 直接调用

```python
from projects.v2_templates.entrypoints import run_render

result = run_render(
    template="bar_chart_race",
    data={
        "date": ["2024-01", "2024-02"],
        "category": ["A", "B"],
        "value": [100, 200]
    },
    brand="corporate"
)
```

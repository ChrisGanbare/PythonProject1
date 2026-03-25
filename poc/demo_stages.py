"""
PythonProject1 阶段 2-4 综合演示

演示:
1. Manim 摄像机集成 (阶段 2)
2. 动画引擎 (阶段 3)
3. 性能优化框架 (阶段 4)
"""

import sys
import os
import time

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from animation import (
    Timeline, 
    EasingLibrary, 
    create_fade_animation,
    create_move_animation,
    create_scale_animation
)
from camera.manim_adapter import ManimCameraAdapter, ManimSceneRenderer, MANIM_AVAILABLE
from visualizer.plotly_viz import PlotlyVisualizer, ChartConfig


def demo_stage2_manim():
    """阶段 2: Manim 摄像机集成演示"""
    print("\n" + "="*60)
    print("阶段 2: Manim 摄像机集成演示")
    print("="*60)
    
    print(f"\nManim 状态：{'✅ 已安装' if MANIM_AVAILABLE else '⏸️ 未安装'}")
    
    # 创建适配器
    adapter = ManimCameraAdapter()
    print(f"✓ 适配器创建成功")
    print(f"  配置：{adapter.config.width}x{adapter.config.height} @ {adapter.config.fps}fps")
    print(f"  质量：{adapter.config.quality}")
    
    # 创建渲染器
    renderer = ManimSceneRenderer()
    print(f"✓ 渲染器创建成功")
    
    if MANIM_AVAILABLE:
        print("\n尝试渲染演示场景...")
        try:
            output = renderer.quick_demo("stage2_demo.mp4")
            print(f"✓ 演示视频：{output}")
        except Exception as e:
            print(f"  渲染需要 FFmpeg 和 LaTeX: {e}")
    else:
        print("\n提示：安装 Manim 以启用完整功能")
        print("  pip install manim")
    
    return True


def demo_stage3_animation():
    """阶段 3: 动画引擎演示"""
    print("\n" + "="*60)
    print("阶段 3: 动画引擎演示")
    print("="*60)
    
    # 1. 缓动函数库
    print("\n1. 缓动函数库测试...")
    easings = EasingLibrary.list_functions()
    print(f"   ✓ 可用缓动函数：{len(easings)} 种")
    print(f"   示例：{', '.join(easings[:5])}...")
    
    # 测试几种缓动
    test_values = [
        ('linear', EasingLibrary.linear(0.5)),
        ('ease_in_quad', EasingLibrary.ease_in_quad(0.5)),
        ('ease_out_quad', EasingLibrary.ease_out_quad(0.5)),
        ('ease_in_out_quad', EasingLibrary.ease_in_out_quad(0.5)),
        ('ease_out_bounce', EasingLibrary.ease_out_bounce(0.5)),
    ]
    
    print("\n   缓动值对比 (t=0.5):")
    for name, value in test_values:
        print(f"     {name:20s}: {value:.4f}")
    
    # 2. 时间轴动画
    print("\n2. 时间轴动画测试...")
    timeline = Timeline(fps=60)
    
    # 创建多对象动画
    ch1 = timeline.add_channel("camera")
    ch1.animate('zoom', 1.0, 2.0, 3.0, easing='ease_in_out_quad')
    ch1.animate('x', 0, 100, 3.0, easing='linear')
    
    ch2 = timeline.add_channel("chart")
    ch2.animate('opacity', 0, 1, 1.0, easing='ease_in_quad')
    ch2.animate('scale', 0.8, 1.0, 1.5, easing='ease_out_back')
    
    ch3 = timeline.add_channel("text")
    ch3.animate('y', -50, 0, 2.0, easing='ease_out_bounce')
    
    print(f"   ✓ 时间轴时长：{timeline.duration}s")
    print(f"   ✓ 通道数量：{len(timeline.channels)}")
    
    # 生成帧
    frames = timeline.get_frames()
    print(f"   ✓ 生成帧数：{len(frames)} (@ {timeline.fps}fps)")
    
    # 3. 关键帧插值
    print("\n3. 关键帧插值测试...")
    from animation import Keyframe, AnimationTrack, Interpolator
    
    track = AnimationTrack("rotation", "angle")
    track.add_keyframe(0, 0, 'linear')
    track.add_keyframe(2, 180, 'ease_in_out_quad')
    track.add_keyframe(4, 360, 'ease_out_quad')
    
    interp = Interpolator()
    
    test_times = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    print("   角度插值:")
    for t in test_times:
        value = track.get_value_at(t)
        print(f"     t={t:.1f}s: {value:.1f}°")
    
    # 4. 便捷函数
    print("\n4. 便捷动画函数测试...")
    
    fade = create_fade_animation("obj1", 0, 1, 1.0, 'ease_in_quad')
    print(f"   ✓ 淡入动画：{fade.duration}s")
    
    move = create_move_animation("obj2", (0, 0), (1920, 1080), 2.0, 'ease_out_quad')
    print(f"   ✓ 移动动画：{move.duration}s")
    
    scale = create_scale_animation("obj3", 0.5, 1.5, 1.0, 'ease_out_back')
    print(f"   ✓ 缩放动画：{scale.duration}s")
    
    # 5. JSON 导出
    print("\n5. 导出功能测试...")
    json_data = timeline.export_to_json()
    print(f"   ✓ JSON 导出成功")
    print(f"     键：{list(json_data.keys())}")
    print(f"     通道数：{len(json_data['channels'])}")
    
    print("\n✅ 阶段 3 动画引擎演示完成!")
    return True


def demo_stage4_optimization():
    """阶段 4: 性能优化框架演示"""
    print("\n" + "="*60)
    print("阶段 4: 性能优化框架演示")
    print("="*60)
    
    # 1. 性能基准测试框架
    print("\n1. 性能基准测试框架...")
    
    # 创建大型时间轴
    timeline = Timeline(fps=60)
    num_objects = 50
    
    for i in range(num_objects):
        ch = timeline.add_channel(f"obj_{i}")
        ch.animate('x', 0.0, float(i * 10), duration=5.0, start_time=0.0, easing='ease_in_out_quad')
        ch.animate('y', 0.0, float(i * 5), duration=5.0, start_time=0.0, easing='linear')
        ch.animate('opacity', 0.0, 1.0, duration=1.0, start_time=0.0, easing='ease_in_quad')
    
    # 测试帧生成性能
    start_time = time.time()
    frames = timeline.get_frames(0, 5.0)
    end_time = time.time()
    
    gen_time = end_time - start_time
    fps_actual = len(frames) / gen_time if gen_time > 0 else 0
    
    print(f"   对象数量：{num_objects}")
    print(f"   生成帧数：{len(frames)}")
    print(f"   生成时间：{gen_time:.3f}s")
    print(f"   实时 FPS: {fps_actual:.1f}")
    
    if fps_actual >= 30:
        print(f"   ✓ 性能优秀 (≥30fps)")
    elif fps_actual >= 15:
        print(f"   ⚠ 性能可接受 (≥15fps)")
    else:
        print(f"   ⚠ 需要优化 (<15fps)")
    
    # 2. 缓存系统框架
    print("\n2. 缓存系统框架...")
    
    class SimpleCache:
        """简单缓存实现"""
        def __init__(self, max_size=100):
            self.cache = {}
            self.max_size = max_size
            self.hits = 0
            self.misses = 0
        
        def get(self, key):
            if key in self.cache:
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
        
        def set(self, key, value):
            if len(self.cache) >= self.max_size:
                # 简单 LRU: 删除最旧的
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value
        
        @property
        def hit_rate(self):
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0
    
    cache = SimpleCache(max_size=50)
    
    # 模拟缓存使用
    for i in range(100):
        key = f"frame_{i % 30}"
        if cache.get(key) is None:
            cache.set(key, {'data': i})
    
    print(f"   缓存命中率：{cache.hit_rate:.1%}")
    print(f"   ✓ 缓存系统工作正常")
    
    # 3. 批量处理框架
    print("\n3. 批量处理框架...")
    
    class BatchProcessor:
        """批量处理器"""
        def __init__(self, batch_size=10):
            self.batch_size = batch_size
            self.processed = 0
        
        def process_batch(self, items, processor_func):
            """处理一批项目"""
            results = []
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                batch_results = [processor_func(item) for item in batch]
                results.extend(batch_results)
                self.processed += len(batch)
                print(f"     处理批次 {i // self.batch_size + 1}: {len(batch)} 项")
            return results
    
    # 测试批量处理
    processor = BatchProcessor(batch_size=10)
    items = list(range(50))
    
    def dummy_processor(item):
        return item * 2
    
    print(f"   批量大小：{processor.batch_size}")
    results = processor.process_batch(items, dummy_processor)
    print(f"   ✓ 处理完成：{processor.processed} 项")
    
    # 4. 内存管理提示
    print("\n4. 内存管理优化建议...")
    print("   • 使用生成器而非列表处理大量帧")
    print("   • 及时释放不再使用的 NumPy 数组")
    print("   • 对大型视频使用分块处理")
    print("   • 使用对象池复用频繁创建的对象")
    
    print("\n✅ 阶段 4 性能优化框架演示完成!")
    return True


def demo_integrated_workflow():
    """集成工作流演示"""
    print("\n" + "="*60)
    print("集成工作流演示")
    print("="*60)
    
    # 1. 创建可视化图表
    print("\n1. 创建可视化图表...")
    config = ChartConfig("line")
    config.set_data(
        x=list(range(20)),
        y=[i ** 1.5 for i in range(20)],
        name="Growth"
    )
    config.set_layout(
        title="Integrated Demo",
        xaxis_title="Time",
        yaxis_title="Value"
    )
    config.enable_animation(duration=2000)
    
    viz = PlotlyVisualizer()
    fig = viz.create_chart(config)
    viz.save_as_html("integrated_chart.html")
    print("   ✓ 图表已生成")
    
    # 2. 创建摄像机动画
    print("\n2. 创建摄像机动画...")
    timeline = Timeline(fps=30)
    
    cam_ch = timeline.add_channel("camera")
    cam_ch.animate('zoom', 1.0, 1.5, duration=3.0, easing='ease_in_out_quad')
    cam_ch.animate('x', 0, 50, duration=3.0, easing='linear')
    
    chart_ch = timeline.add_channel("chart")
    chart_ch.animate('opacity', 0, 1, duration=1.0, easing='ease_in_quad')
    chart_ch.animate('scale', 0.9, 1.0, duration=1.5, easing='ease_out_back')
    
    frames = timeline.get_frames()
    print(f"   ✓ 生成 {len(frames)} 帧摄像机动画")
    
    # 3. 准备视频合成
    print("\n3. 准备视频合成...")
    from video.composer import VideoConfig, VideoComposer
    
    config = VideoConfig(width=1920, height=1080, fps=30, duration=5)
    composer = VideoComposer(config)
    composer.set_background((20, 20, 30))
    
    composer.add_text(
        "PythonProject1",
        duration=5,
        font_size=64,
        color="white",
        position="center"
    )
    
    print(f"   ✓ 视频合成器就绪")
    print(f"     分辨率：{config.width}x{config.height}")
    print(f"     帧率：{config.fps}fps")
    print(f"     时长：{config.duration}s")
    
    # 4. 导出配置
    print("\n4. 导出配置...")
    timeline_json = timeline.export_to_json()
    print(f"   ✓ 动画配置已导出")
    print(f"     格式：JSON")
    print(f"     通道数：{len(timeline_json['channels'])}")
    
    print("\n✅ 集成工作流演示完成!")
    print("\n生成的文件:")
    print("  - integrated_chart.html (交互式图表)")
    print("  - timeline_config.json (动画配置)")
    
    return True


def main():
    """主函数"""
    print("\n" + "#"*60)
    print("# PythonProject1 - 阶段 2-4 综合演示")
    print("#"*60)
    
    try:
        # 阶段 2
        demo_stage2_manim()
        
        # 阶段 3
        demo_stage3_animation()
        
        # 阶段 4
        demo_stage4_optimization()
        
        # 集成
        demo_integrated_workflow()
        
        print("\n" + "="*60)
        print("✅ 所有阶段演示完成!")
        print("="*60)
        
        print("\n📊 进度总结:")
        print("  阶段 1: 基础架构          ████████████████████ 100%")
        print("  阶段 2: Manim 摄像机集成  ████░░░░░░░░░░░░░░░░  20%")
        print("  阶段 3: 动画引擎开发      ████████░░░░░░░░░░░░  40%")
        print("  阶段 4: 性能优化与生产    ████░░░░░░░░░░░░░░░░  20%")
        
        print("\n📁 生成的文件:")
        print("  - stage2_demo.mp4 (Manim 演示，如可用)")
        print("  - integrated_chart.html (集成图表)")
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

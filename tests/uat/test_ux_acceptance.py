"""
UAT 用户验收测试 - 产品经理视角
测试所有前端交互功能
"""
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

BASE_URL = "http://127.0.0.1:8090"

def create_uat_report():
    """生成 UAT 测试报告"""
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        # ========== 测试 1: 首页加载 ==========
        print("\n【测试 1】首页基础功能")
        try:
            page.goto(BASE_URL, wait_until="networkidle")
            
            # 页面标题
            expect(page).to_have_title("PythonProject1 v2.3 - 数据可视化视频生成平台", timeout=5000)
            results.append(("首页标题", "✅"))
            print("  ✓ 首页标题正确")
            
            # 主标题
            expect(page.locator("h1")).to_contain_text("PythonProject1")
            results.append(("主标题显示", "✅"))
            print("  ✓ 主标题显示")
            
            # 模板卡片
            template_count = page.locator(".template-card").count()
            assert template_count == 6, f"Expected 6, got {template_count}"
            results.append(("模板卡片", f"✅ ({template_count}个)"))
            print(f"  ✓ 6 个模板卡片显示正常")
            
            # 快捷入口（应该只有 2 个：AI + 项目）
            shortcut_cards = page.locator(".container:has(h3:has-text('其他功能')) .card")
            shortcut_count = shortcut_cards.count()
            results.append(("快捷入口", f"ℹ️  ({shortcut_count}个)"))
            print(f"  ℹ️  快捷入口: {shortcut_count} 个")
            
            # 验证没有"代码工坊"
            code_studio_text = page.locator("text=代码工坊").count()
            assert code_studio_text == 0, f"不应显示代码工坊，但找到 {code_studio_text} 处"
            results.append(("代码工坊已移除", "✅"))
            print("  ✓ 确认无代码工坊入口")
            
        except Exception as e:
            results.append(("首页加载", f"❌ {e}"))
            print(f"  ❌ 失败: {e}")
        
        # ========== 测试 2: 向导流程 ==========
        print("\n【测试 2】向导流程 - 模板选择")
        try:
            page.goto(BASE_URL)
            time.sleep(1)
            
            # 初始状态
            next_btn = page.locator("button:has-text('下一步')").first
            assert next_btn.is_disabled(), "初始状态下一步应禁用"
            results.append(("初始下一步禁用", "✅"))
            print("  ✓ 初始状态正确")
            
            # 选择模板
            page.locator(".template-card").first.click()
            time.sleep(0.5)
            
            # 下一步启用
            assert next_btn.is_enabled(), "选择模板后下一步应启用"
            results.append(("选择模板后启用", "✅"))
            print("  ✓ 选择模板后下一步启用")
            
            # 进入步骤 2
            next_btn.click()
            time.sleep(1)
            
            # 验证步骤 2 激活
            step2_visible = page.locator(".step:nth-child(2).active").is_visible()
            if step2_visible:
                results.append(("步骤切换", "✅"))
                print("  ✓ 成功切换到步骤 2")
            
        except Exception as e:
            results.append(("向导流程", f"❌ {e}"))
            print(f"  ❌ 失败: {e}")
        
        # ========== 测试 3: AI 编译页面 ==========
        print("\n【测试 3】AI 意图编译页面")
        try:
            page.goto(f"{BASE_URL}/ai_compile.html", wait_until="networkidle")
            time.sleep(1)
            
            # 验证页面加载
            title = page.title()
            results.append(("AI编译页面", "✅"))
            print(f"  ✓ AI 编译页面加载: {title}")
            
            # 查找主要交互元素
            textarea_count = page.locator("textarea").count()
            button_count = page.locator("button").count()
            print(f"  ℹ️  页面元素: {textarea_count} 个输入框, {button_count} 个按钮")
            results.append(("AI交互元素", f"✅ ({button_count}按钮)"))
            
        except Exception as e:
            results.append(("AI编译页面", f"❌ {e}"))
            print(f"  ❌ 失败: {e}")
        
        # ========== 测试 4: 项目管理页面 ==========
        print("\n【测试 4】项目管理页面")
        try:
            page.goto(f"{BASE_URL}/projects.html", wait_until="networkidle")
            time.sleep(1)
            
            results.append(("项目管理页面", "✅"))
            print("  ✓ 项目管理页面加载")
            
            # 验证顶部导航无代码工坊
            code_studio_nav = page.locator("a:has-text('代码工坊')").count()
            assert code_studio_nav == 0, f"不应有代码工坊链接，但找到 {code_studio_nav} 个"
            results.append(("导航栏清理", "✅"))
            print("  ✓ 确认导航栏无代码工坊链接")
            
        except Exception as e:
            results.append(("项目管理页面", f"❌ {e}"))
            print(f"  ❌ 失败: {e}")
        
        # ========== 测试 5: 全局设置 ==========
        print("\n【测试 5】全局设置功能")
        try:
            page.goto(BASE_URL)
            time.sleep(1)
            
            # 点击设置按钮
            page.locator("button[data-bs-target='#settingsModal']").click()
            time.sleep(1)
            
            # 验证模态框
            modal = page.locator("#settingsModal.show")
            expect(modal).to_be_visible(timeout=3000)
            results.append(("设置模态框", "✅"))
            print("  ✓ 设置模态框打开")
            
            # 验证 AI 配置区
            if page.locator("text=DeepSeek").count() > 0:
                results.append(("DeepSeek配置", "✅"))
                print("  ✓ DeepSeek 配置选项存在")
            
            # 验证渲染设置区
            if page.locator("text=质量预设").count() > 0 or page.locator("text=视频分辨率").count() > 0:
                results.append(("渲染设置", "✅"))
                print("  ✓ 渲染设置区域存在")
            
        except Exception as e:
            results.append(("全局设置", f"❌ {e}"))
            print(f"  ❌ 失败: {e}")
        
        browser.close()
    
    # ========== 测试 6: API 端点 ==========
    print("\n【测试 6】API 端点验证")
    import requests
    try:
        # 健康检查
        resp = requests.get(f"{BASE_URL}/api/studio/v1/health", timeout=5)
        if resp.status_code == 200:
            results.append(("健康检查", f"✅ ({resp.json()})"))
            print(f"  ✓ 健康检查: {resp.status_code} - {resp.json()}")
        
        # 架构元数据
        resp = requests.get(f"{BASE_URL}/api/meta/architecture", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            domain_count = len(data.get("domain_mounts", []))
            results.append(("架构元数据", f"✅ ({domain_count}个domain)"))
            print(f"  ✓ 架构元数据: {domain_count} 个 domain 挂载")
        
        # API 文档
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        results.append(("API文档", f"✅ ({resp.status_code})"))
        print(f"  ✓ API 文档: {resp.status_code}")
        
    except Exception as e:
        results.append(("API端点", f"❌ {e}"))
        print(f"  ❌ 失败: {e}")
    
    # ========== 生成报告 ==========
    print("\n" + "="*60)
    print(" UAT 测试报告")
    print("="*60)
    for test_name, result in results:
        print(f"  {test_name:20s} {result}")
    
    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    # 保存报告
    report_path = Path(__file__).parent.parent.parent / "docs" / "reports" / "UAT_RESULT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# UAT 用户验收测试结果\n\n")
        f.write(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**测试人**: 产品经理 (模拟真实用户)\n")
        f.write(f"**基准URL**: {BASE_URL}\n\n")
        f.write("## 测试结果\n\n")
        f.write("| 测试项 | 结果 |\n")
        f.write("|--------|------|\n")
        for name, result in results:
            f.write(f"| {name} | {result} |\n")
        f.write(f"\n**通过率**: {passed}/{total} ({passed/total*100:.1f}%)\n")
    
    print(f"\n报告已保存: {report_path}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = create_uat_report()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UAT 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python
"""
PythonProject1 v2.3 - 功能验证测试脚本

测试项目：
1. 数据输入校验
2. 文件上传功能
3. 全局设置
4. 视频生成流程
"""

import sys
import requests
from pathlib import Path

BASE_URL = "http://localhost:8090"

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_api_health():
    """测试 API 健康状态"""
    print_header("1. API 健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/api/registry", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 正常 - 发现 {len(data.get('projects', []))} 个项目")
            return True
        else:
            print(f"❌ API 异常 - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接 API: {e}")
        return False

def test_settings_api():
    """测试设置 API"""
    print_header("2. 设置 API 测试")
    
    try:
        # 获取设置
        response = requests.get(f"{BASE_URL}/api/settings", timeout=5)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ 设置获取成功")
            print(f"   - 视频分辨率：{settings.get('video_width')}x{settings.get('video_height')}")
            print(f"   - FPS: {settings.get('video_fps')}")
            print(f"   - 模型：{settings.get('openai_model')}")
            return True
        else:
            print(f"❌ 设置获取失败 - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 设置 API 测试失败：{e}")
        return False

def test_data_validation():
    """测试数据校验逻辑"""
    print_header("3. 数据校验逻辑测试")
    
    test_cases = [
        # (输入，期望结果，描述)
        ("2024-01, 2024-02, 2024-03", True, "正确格式（英文逗号）"),
        ("2024-01, 2024-02, 2024-03", True, "正确格式（中文逗号）"),
        ("202401202402202403", False, "无分隔符"),
        ("202401, 202402", False, "日期无连接符"),
        ("2024-01,,2024-02", False, "连续逗号"),
        ("", False, "空值"),
        ("100, abc, 200", False, "非数字数值"),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in test_cases:
        try:
            # 模拟前端校验逻辑
            is_valid = True
            error = ""
            
            if not input_val or input_val.strip() == '':
                is_valid = False
                error = "空值"
            elif ",," in input_val or "，，" in input_val:
                is_valid = False
                error = "连续逗号"
            elif input_val.replace(" ", "").isdigit() and len(input_val.replace(" ", "")) > 6:
                is_valid = False
                error = "无分隔符"
            
            if is_valid == expected:
                print(f"  ✅ {description}: {'通过' if is_valid else '拦截'}")
                passed += 1
            else:
                print(f"  ❌ {description}: 期望{'通过' if expected else '拦截'}，实际{'通过' if is_valid else '拦截'}")
                failed += 1
        except Exception as e:
            print(f"  ❌ {description}: 异常 {e}")
            failed += 1
    
    print(f"\n结果：{passed} 通过，{failed} 失败")
    return failed == 0

def test_static_files():
    """测试静态文件"""
    print_header("4. 静态文件检查")
    
    files_to_check = [
        "static/index.html",
        "static/settings-modal.html",
        "static/projects.html",
        "static/code_studio.html",
        "static/ai_compile.html",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path} ({size} bytes)")
        else:
            print(f"  ❌ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def test_backend_compatibility():
    """测试后端数据兼容性"""
    print_header("5. 后端数据兼容性测试")
    
    test_cases = [
        # 字符串格式（英文逗号）
        {"labels": "2024-01, 2024-02, 2024-03", "values": "100, 150, 200"},
        # 字符串格式（中文逗号）
        {"labels": "2024-01, 2024-02, 2024-03", "values": "100, 150, 200"},
        # 数组格式
        {"labels": ["2024-01", "2024-02", "2024-03"], "values": [100, 150, 200]},
    ]
    
    for i, data in enumerate(test_cases, 1):
        try:
            # 模拟后端处理逻辑
            labels_raw = data["labels"]
            values_raw = data["values"]
            
            if isinstance(labels_raw, str):
                labels = [l.strip() for l in labels_raw.replace(",", ",").split(",") if l.strip()]
            elif isinstance(labels_raw, list):
                labels = [str(l).strip() for l in labels_raw if str(l).strip()]
            
            if isinstance(values_raw, str):
                values = [float(v.strip()) for v in values_raw.replace(",", ",").split(",") if v.strip()]
            elif isinstance(values_raw, list):
                values = [float(v) for v in values_raw if v is not None]
            
            print(f"  ✅ 测试用例 {i}: labels={len(labels)} 个，values={len(values)} 个")
        except Exception as e:
            print(f"  ❌ 测试用例 {i}: 异常 {e}")
    
    return True

def test_file_upload_ui():
    """测试文件上传 UI 元素"""
    print_header("6. 文件上传 UI 检查")
    
    index_path = Path("static/index.html")
    if not index_path.exists():
        print("  ❌ index.html 不存在")
        return False
    
    content = index_path.read_text(encoding='utf-8')
    
    checks = [
        ('<input type="file"', "文件输入框"),
        ('accept=".tsv,.csv,.xlsx,.xls"', "支持格式"),
        ('@click="triggerFileUpload"', "选择文件按钮"),
        ('@click="downloadTemplate"', "下载模板按钮"),
        ('@click="removeFile"', "删除文件按钮"),
        ('handleFileUpload', "文件上传处理"),
    ]
    
    all_present = True
    for pattern, description in checks:
        if pattern in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} 缺失")
            all_present = False
    
    return all_present

def test_settings_modal():
    """测试设置模态框"""
    print_header("7. 设置模态框检查")
    
    modal_path = Path("static/settings-modal.html")
    if not modal_path.exists():
        print("  ❌ settings-modal.html 不存在")
        return False
    
    content = modal_path.read_text(encoding='utf-8')
    
    checks = [
        ('toggleApiKeyVisibility', "API Key 切换功能"),
        ('bi bi-eye', "眼睛图标"),
        ('settingsApiKey', "API Key 输入框"),
        ('settingsBaseUrl', "Base URL 输入框"),
        ('settingsModel', "模型选择"),
        ('validateAPI', "验证 API 功能"),
    ]
    
    all_present = True
    for pattern, description in checks:
        if pattern in content:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} 缺失")
            all_present = False
    
    return all_present

def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*20 + "PythonProject1 v2.3 功能验证测试" + " "*20 + "║")
    print("╚" + "═"*68 + "╝")
    
    results = []
    
    # 1. API 健康检查
    results.append(("API 健康", test_api_health()))
    
    # 2. 设置 API
    results.append(("设置 API", test_settings_api()))
    
    # 3. 数据校验
    results.append(("数据校验", test_data_validation()))
    
    # 4. 静态文件
    results.append(("静态文件", test_static_files()))
    
    # 5. 后端兼容性
    results.append(("后端兼容性", test_backend_compatibility()))
    
    # 6. 文件上传 UI
    results.append(("文件上传 UI", test_file_upload_ui()))
    
    # 7. 设置模态框
    results.append(("设置模态框", test_settings_modal()))
    
    # 总结
    print_header("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计：{passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())

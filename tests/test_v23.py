"""
v2.3 自动化测试脚本

运行所有测试用例并生成报告
"""

import sys
import time
from pathlib import Path

# 测试配置
BASE_URL = "http://localhost:8090"
TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "total": 0
}


def print_header(text):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def test_api_endpoint(name, url, method="GET", data=None):
    """测试 API 端点"""
    import requests
    
    TEST_RESULTS["total"] += 1
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        
        if response.status_code in [200, 201]:
            print(f"  ✓ {name}: {response.status_code}")
            TEST_RESULTS["passed"] += 1
            return True, response.json()
        else:
            print(f"  ✗ {name}: {response.status_code}")
            TEST_RESULTS["failed"] += 1
            return False, None
            
    except Exception as e:
        print(f"  ✗ {name}: {str(e)}")
        TEST_RESULTS["failed"] += 1
        return False, None


def run_tests():
    """运行所有测试"""
    import requests
    
    print_header("PythonProject1 v2.3 自动化测试")
    
    # 检查服务是否可用
    print("\n[前置检查] 检查 Dashboard 服务...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"  ✓ Dashboard 服务可用：{response.status_code}")
    except Exception as e:
        print(f"  ✗ Dashboard 服务不可用：{e}")
        print("\n请先启动 Dashboard:")
        print("  python scripts/dashboard.py")
        return False
    
    # 测试 API 端点
    print_header("1. API 接口测试")
    
    # v2 API
    test_api_endpoint("GET /api/v2/templates", "/api/v2/templates")
    test_api_endpoint("GET /api/v2/brands", "/api/v2/brands")
    
    # v1 API
    test_api_endpoint("GET /api/v1/templates", "/api/v1/templates")
    test_api_endpoint("GET /api/v1/themes", "/api/v1/themes")
    test_api_endpoint("GET /api/registry", "/api/registry")
    
    # 测试视频创建流程
    print_header("2. 视频创建流程测试")
    
    # 创建视频
    create_data = {
        "template": {
            "template_id": "bar_chart_race",
            "template_name": "柱状图竞赛"
        },
        "data": {
            "input_mode": "manual",
            "labels": "2024-01,2024-02,2024-03",
            "values": "100,150,200",
            "series_name": "销售额"
        },
        "brand": {
            "brand_id": "corporate"
        },
        "platform": "bilibili"
    }
    
    success, result = test_api_endpoint(
        "POST /api/v2/create",
        "/api/v2/create",
        method="POST",
        data=create_data
    )
    
    if success and result:
        job_id = result.get("job_id")
        print(f"  → 作业 ID: {job_id}")
        
        # 轮询查询状态
        print("\n  轮询作业状态...")
        for i in range(10):
            time.sleep(1)
            success, status = test_api_endpoint(
                f"GET /api/v2/status/{job_id}",
                f"/api/v2/status/{job_id}"
            )
            
            if success and status:
                if status.get("status") == "completed":
                    print(f"  ✓ 视频生成完成：{status.get('output_path')}")
                    break
                elif status.get("status") == "failed":
                    print(f"  ✗ 视频生成失败：{status.get('error')}")
                    break
                else:
                    print(f"  → 进度：{status.get('progress')}% - {status.get('message')}")
    
    # 测试前端页面
    print_header("3. 前端页面测试")
    
    pages = [
        ("/", "首页"),
        ("/ai_compile.html", "AI 意图编译"),
        ("/projects.html", "项目管理"),
        ("/code_studio.html", "代码工坊"),
        ("/classic", "旧版 Dashboard"),
        ("/v2", "v2 展示页")
    ]
    
    for path, name in pages:
        TEST_RESULTS["total"] += 1
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                print(f"  ✓ {name}: {response.status_code} ({len(response.content)} bytes)")
                TEST_RESULTS["passed"] += 1
            else:
                print(f"  ✗ {name}: {response.status_code}")
                TEST_RESULTS["failed"] += 1
        except Exception as e:
            print(f"  ✗ {name}: {str(e)}")
            TEST_RESULTS["failed"] += 1
    
    # 生成报告
    print_header("测试报告")
    
    print(f"\n总计：{TEST_RESULTS['total']} 个测试")
    print(f"通过：{TEST_RESULTS['passed']} ✓")
    print(f"失败：{TEST_RESULTS['failed']} ✗")
    
    if TEST_RESULTS['total'] > 0:
        pass_rate = TEST_RESULTS['passed'] / TEST_RESULTS['total'] * 100
        print(f"通过率：{pass_rate:.1f}%")
    
    # 保存报告
    report_path = Path(__file__).parent.parent / "TEST_RESULTS.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"PythonProject1 v2.3 测试结果\n")
        f.write(f"{'='*40}\n")
        f.write(f"总计：{TEST_RESULTS['total']} 个测试\n")
        f.write(f"通过：{TEST_RESULTS['passed']} ✓\n")
        f.write(f"失败：{TEST_RESULTS['failed']} ✗\n")
        if TEST_RESULTS['total'] > 0:
            f.write(f"通过率：{pass_rate:.1f}%\n")
        f.write(f"\n测试时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\n报告已保存到：{report_path}")
    
    return TEST_RESULTS['failed'] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

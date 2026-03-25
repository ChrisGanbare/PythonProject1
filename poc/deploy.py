"""
生产部署脚本

功能:
- 环境检查
- 依赖安装
- 配置生成
- 部署执行
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional


class DeploymentManager:
    """部署管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.poc_dir = self.project_root / "poc"
        self.docker_dir = self.project_root / "docker"
        self.workspace_dir = self.project_root / "workspace"
        
    def check_python_version(self) -> bool:
        """检查 Python 版本"""
        version = sys.version_info
        required = (3, 9)
        
        if version >= required:
            print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            print(f"✗ Python {required[0]}.{required[1]}+ required")
            return False
    
    def check_dependencies(self) -> List[str]:
        """检查依赖"""
        missing = []
        
        required_packages = [
            'plotly',
            'numpy',
            'pandas',
            'PIL',
            'pytest'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package}")
            except ImportError:
                print(f"✗ {package}")
                missing.append(package)
        
        return missing
    
    def check_ffmpeg(self) -> bool:
        """检查 FFmpeg"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ FFmpeg: {result.stdout.split()[2]}")
                return True
        except Exception:
            pass
        
        print("✗ FFmpeg not found")
        return False
    
    def check_docker(self) -> bool:
        """检查 Docker"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ Docker: {result.stdout.strip()}")
                return True
        except Exception:
            pass
        
        print("✗ Docker not found")
        return False
    
    def install_dependencies(self, upgrade: bool = False) -> bool:
        """安装依赖"""
        requirements_file = self.poc_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("✗ requirements.txt not found")
            return False
        
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
        
        if upgrade:
            cmd.append("--upgrade")
        
        print(f"Installing dependencies...")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ Dependencies installed")
            return True
        else:
            print("✗ Installation failed")
            return False
    
    def run_tests(self) -> bool:
        """运行测试"""
        test_dir = self.poc_dir / "tests"
        
        if not test_dir.exists():
            print("✗ Test directory not found")
            return False
        
        cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v"]
        
        print(f"\nRunning tests...")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ All tests passed")
            return True
        else:
            print("✗ Some tests failed")
            return False
    
    def run_demo(self) -> bool:
        """运行演示"""
        demo_file = self.poc_dir / "demo_stages.py"
        
        if not demo_file.exists():
            print("✗ Demo file not found")
            return False
        
        cmd = [sys.executable, str(demo_file)]
        
        print(f"\nRunning demo...")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ Demo completed")
            return True
        else:
            print("✗ Demo failed")
            return False
    
    def build_docker(self) -> bool:
        """构建 Docker 镜像"""
        if not self.docker_dir.exists():
            print("✗ Docker directory not found")
            return False
        
        cmd = [
            "docker", "build",
            "-f", str(self.docker_dir / "Dockerfile"),
            "-t", "pythonproject1:latest",
            str(self.project_root)
        ]
        
        print(f"\nBuilding Docker image...")
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("✓ Docker image built")
            return True
        else:
            print("✗ Docker build failed")
            return False
    
    def create_workspace(self) -> bool:
        """创建工作目录"""
        dirs = [
            self.workspace_dir,
            self.workspace_dir / "output",
            self.workspace_dir / "temp",
            self.workspace_dir / "cache"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created {dir_path}")
        
        return True
    
    def generate_config(self) -> bool:
        """生成配置文件"""
        config_content = """# PythonProject1 配置文件

# 视频编码配置
[video]
width = 1920
height = 1080
fps = 30
bitrate = 5000k
codec = libx264

# 音频配置
[audio]
codec = aac
bitrate = 192k
sample_rate = 44100

# 性能配置
[performance]
max_workers = 4
cache_enabled = true
hardware_accel = false

# 输出配置
[output]
format = mp4
quality = high
"""
        
        config_file = self.workspace_dir / "config.ini"
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Generated config: {config_file}")
        return True
    
    def full_deployment(self) -> bool:
        """完整部署流程"""
        print("="*60)
        print("PythonProject1 完整部署")
        print("="*60)
        
        steps = [
            ("环境检查", self.check_environment),
            ("创建工作目录", self.create_workspace),
            ("安装依赖", lambda: self.install_dependencies(upgrade=False)),
            ("生成配置", self.generate_config),
            ("运行测试", self.run_tests),
            ("运行演示", self.run_demo),
        ]
        
        success_count = 0
        
        for step_name, step_func in steps:
            print(f"\n{'='*60}")
            print(f"步骤：{step_name}")
            print(f"{'='*60}")
            
            try:
                if step_func():
                    success_count += 1
            except Exception as e:
                print(f"✗ Error: {e}")
        
        # 总结
        print(f"\n{'='*60}")
        print(f"部署完成：{success_count}/{len(steps)} 步骤成功")
        print(f"{'='*60}")
        
        return success_count == len(steps)
    
    def check_environment(self) -> bool:
        """检查环境"""
        print("\n环境检查:")
        
        checks = [
            ("Python 版本", self.check_python_version),
            ("FFmpeg", self.check_ffmpeg),
            ("Docker", self.check_docker),
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n{check_name}:")
            if not check_func():
                all_passed = False
        
        # 检查 Python 依赖
        print("\nPython 依赖:")
        missing = self.check_dependencies()
        if missing:
            print(f"\n缺少依赖：{', '.join(missing)}")
            print("运行：pip install -r requirements.txt")
            all_passed = False
        
        return all_passed


def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 创建部署管理器
    manager = DeploymentManager(project_root)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            success = manager.check_environment()
        elif command == "install":
            success = manager.install_dependencies()
        elif command == "test":
            success = manager.run_tests()
        elif command == "demo":
            success = manager.run_demo()
        elif command == "docker":
            success = manager.build_docker()
        elif command == "deploy":
            success = manager.full_deployment()
        else:
            print(f"Unknown command: {command}")
            print("Commands: check, install, test, demo, docker, deploy")
            success = False
    else:
        # 默认运行完整部署
        success = manager.full_deployment()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

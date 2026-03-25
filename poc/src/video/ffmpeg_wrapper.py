"""
FFmpeg 封装模块 - 高性能视频处理

功能:
- 直接 FFmpeg 调用 (绕过 MoviePy)
- 硬件加速支持
- 批量编码
- 流式处理
"""

import subprocess
import json
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass
class FFmpegConfig:
    """FFmpeg 配置"""
    # 视频编码
    video_codec: str = "libx264"
    video_bitrate: str = "5000k"
    video_preset: str = "medium"  # ultrafast, fast, medium, slow, veryslow
    crf: int = 23  # 18-28, 越低质量越高
    
    # 分辨率
    width: int = 1920
    height: int = 1080
    fps: int = 30
    
    # 音频编码
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    audio_sample_rate: int = 44100
    
    # 硬件加速
    hardware_accel: bool = False
    gpu_encoder: str = "h264_nvenc"  # nvidia, h264_amf (amd), h264_videotoolbox (mac)
    
    # 输出格式
    output_format: str = "mp4"
    pixel_format: str = "yuv420p"
    
    def get_video_filter(self) -> str:
        """获取视频滤镜字符串"""
        filters = []
        
        # 缩放
        if self.width and self.height:
            filters.append(f"scale={self.width}:{self.height}")
        
        # 帧率
        if self.fps:
            filters.append(f"fps={self.fps}")
        
        return ",".join(filters) if filters else None
    
    def build_command(self, input_path: str, output_path: str,
                      extra_args: Optional[List[str]] = None) -> List[str]:
        """构建 FFmpeg 命令"""
        cmd = ["ffmpeg", "-y"]  # -y 覆盖输出文件
        
        # 输入
        cmd.extend(["-i", input_path])
        
        # 视频编码
        if self.hardware_accel:
            cmd.extend(["-c:v", self.gpu_encoder])
        else:
            cmd.extend(["-c:v", self.video_codec])
            cmd.extend(["-crf", str(self.crf)])
            cmd.extend(["-preset", self.video_preset])
        
        # 视频滤镜
        video_filter = self.get_video_filter()
        if video_filter:
            cmd.extend(["-vf", video_filter])
        
        # 音频编码
        cmd.extend(["-c:a", self.audio_codec])
        cmd.extend(["-b:a", self.audio_bitrate])
        cmd.extend(["-ar", str(self.audio_sample_rate)])
        
        # 像素格式
        cmd.extend(["-pix_fmt", self.pixel_format])
        
        # 额外参数
        if extra_args:
            cmd.extend(extra_args)
        
        # 输出
        cmd.append(output_path)
        
        return cmd


class FFmpegWrapper:
    """
    FFmpeg 封装
    
    提供高性能视频处理能力
    """
    
    def __init__(self, config: Optional[FFmpegConfig] = None):
        self.config = config or FFmpegConfig()
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> str:
        """查找 FFmpeg 可执行文件"""
        # 尝试在 PATH 中查找
        ffmpeg = self._which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        
        # 常见安装位置
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return "ffmpeg"  # 假设在 PATH 中
    
    def _which(self, executable: str) -> Optional[str]:
        """查找可执行文件"""
        try:
            result = subprocess.run(
                ["where" if os.name == "nt" else "which", executable],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        return None
    
    def check_available(self) -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_version(self) -> str:
        """获取 FFmpeg 版本"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.split('\n')[0]
        except Exception as e:
            return f"Error: {e}"
    
    def encode(self, input_path: str, output_path: str,
               config: Optional[FFmpegConfig] = None,
               show_progress: bool = True) -> Tuple[bool, str]:
        """
        编码视频
        
        Args:
            input_path: 输入文件
            output_path: 输出文件
            config: 配置 (None 使用默认)
            show_progress: 显示进度
            
        Returns:
            (成功标志，消息)
        """
        if config is None:
            config = self.config
        
        # 检查输入文件
        if not os.path.exists(input_path):
            return False, f"Input file not found: {input_path}"
        
        # 构建命令
        cmd = config.build_command(input_path, output_path)
        
        # 执行
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 小时超时
            )
            
            if result.returncode == 0:
                return True, f"Encoded successfully: {output_path}"
            else:
                return False, f"FFmpeg error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Encoding timed out"
        except Exception as e:
            return False, f"Error: {e}"
    
    def create_video_from_images(self, image_pattern: str, output_path: str,
                                  fps: int = 30) -> Tuple[bool, str]:
        """
        从图片序列创建视频
        
        Args:
            image_pattern: 图片模式 (如 "frame_%04d.png")
            output_path: 输出文件
            fps: 帧率
            
        Returns:
            (成功标志，消息)
        """
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", image_pattern,
            "-c:v", self.config.video_codec,
            "-pix_fmt", self.config.pixel_format,
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                return True, f"Created video: {output_path}"
            return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def extract_audio(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """提取音频"""
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "copy",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return True, f"Extracted audio: {output_path}"
            return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def get_video_info(self, input_path: str) -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            input_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None
    
    def concat_videos(self, video_files: List[str], output_path: str) -> Tuple[bool, str]:
        """
        拼接视频
        
        Args:
            video_files: 视频文件列表
            output_path: 输出文件
            
        Returns:
            (成功标志，消息)
        """
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")
            list_file = f.name
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            os.unlink(list_file)
            
            if result.returncode == 0:
                return True, f"Concatenated {len(video_files)} videos"
            return False, result.stderr
        except Exception as e:
            os.unlink(list_file)
            return False, str(e)
    
    def trim_video(self, input_path: str, output_path: str,
                   start: float, duration: float) -> Tuple[bool, str]:
        """
        裁剪视频
        
        Args:
            input_path: 输入文件
            output_path: 输出文件
            start: 开始时间 (秒)
            duration: 时长 (秒)
        """
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                return True, f"Trimmed video: {start}s-{start+duration}s"
            return False, result.stderr
        except Exception as e:
            return False, str(e)


class BatchVideoProcessor:
    """
    批量视频处理器
    """
    
    def __init__(self, ffmpeg_wrapper: Optional[FFmpegWrapper] = None,
                 max_workers: int = 4):
        self.ffmpeg = ffmpeg_wrapper or FFmpegWrapper()
        self.max_workers = max_workers
        self.results = []
    
    def process_batch(self, jobs: List[Dict]) -> List[Dict]:
        """
        批量处理任务
        
        Args:
            jobs: 任务列表，每项包含 input_path, output_path, config
            
        Returns:
            处理结果列表
        """
        results = []
        
        for i, job in enumerate(jobs):
            input_path = job.get('input_path')
            output_path = job.get('output_path')
            config = job.get('config')
            
            if not input_path or not output_path:
                results.append({
                    'index': i,
                    'success': False,
                    'error': 'Missing input_path or output_path'
                })
                continue
            
            success, message = self.ffmpeg.encode(input_path, output_path, config)
            
            results.append({
                'index': i,
                'success': success,
                'message': message,
                'input': input_path,
                'output': output_path
            })
            
            print(f"[{i+1}/{len(jobs)}] {'✓' if success else '✗'} {message}")
        
        self.results = results
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取处理摘要"""
        total = len(self.results)
        success = sum(1 for r in self.results if r['success'])
        failed = total - success
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': success / total if total > 0 else 0
        }


# 便捷函数
def quick_encode(input_path: str, output_path: str,
                 quality: str = "high") -> bool:
    """快速编码视频"""
    ffmpeg = FFmpegWrapper()
    
    if not ffmpeg.check_available():
        print("FFmpeg not available")
        return False
    
    config = FFmpegConfig()
    
    if quality == "low":
        config.crf = 28
        config.video_preset = "fast"
    elif quality == "medium":
        config.crf = 23
        config.video_preset = "medium"
    elif quality == "high":
        config.crf = 18
        config.video_preset = "slow"
    
    success, message = ffmpeg.encode(input_path, output_path, config)
    print(message)
    return success


if __name__ == "__main__":
    print("Testing FFmpegWrapper...\n")
    
    ffmpeg = FFmpegWrapper()
    
    # 检查可用性
    available = ffmpeg.check_available()
    print(f"FFmpeg 可用：{'✅ 是' if available else '❌ 否'}")
    
    if available:
        version = ffmpeg.get_version()
        print(f"版本：{version}")
        
        # 测试配置
        config = FFmpegConfig()
        print(f"\n默认配置:")
        print(f"  编码器：{config.video_codec}")
        print(f"  分辨率：{config.width}x{config.height}")
        print(f"  帧率：{config.fps}")
        print(f"  CRF: {config.crf}")
    else:
        print("\n⚠️ FFmpeg 未安装")
        print("安装方法:")
        print("  Windows: choco install ffmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
    
    print("\n✅ FFmpeg wrapper test complete!")

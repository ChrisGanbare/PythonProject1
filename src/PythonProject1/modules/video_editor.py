"""
视频编辑模块
FFmpeg 命令行包装，支持视频拼接、字幕、音乐混音等
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import shutil

from config.settings import settings
from models.exceptions import RenderError
from utils.decorators import retry, log_execution


logger = logging.getLogger(__name__)


class VideoEditor:
    """视频编辑器（FFmpeg 包装）"""
    
    def __init__(self):
        """初始化编辑器"""
        self.ffmpeg_path = shutil.which('ffmpeg')
        if not self.ffmpeg_path:
            raise RenderError("未找到 FFmpeg，请先安装", step="initialization")
        
        logger.info(f"[VideoEditor] FFmpeg 路径: {self.ffmpeg_path}")
    
    @retry(max_attempts=2, backoff_factor=2.0, exceptions=(subprocess.CalledProcessError,))
    @log_execution(log_level="info")
    def add_subtitle(
        self,
        input_video: Path,
        subtitle_file: Path,
        output_video: Path,
        subtitle_codec: str = "mov_text",
    ) -> Path:
        """
        添加字幕到视频
        
        Args:
            input_video: 输入视频路径
            subtitle_file: 字幕文件路径（.srt 或 .vtt）
            output_video: 输出视频路径
            subtitle_codec: 字幕编码（mov_text/subrip/ass）
        
        Returns:
            输出文件路径
        
        Raises:
            RenderError: 操作失败
        """
        if not input_video.exists():
            raise RenderError(f"输入视频不存在: {input_video}", step="add_subtitle")
        
        if not subtitle_file.exists():
            raise RenderError(f"字幕文件不存在: {subtitle_file}", step="add_subtitle")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(input_video),
            "-i", str(subtitle_file),
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", subtitle_codec,
            "-y",
            str(output_video),
        ]
        
        try:
            logger.debug(f"[FFmpeg] 命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RenderError(
                    f"字幕添加失败",
                    step="add_subtitle",
                    ffmpeg_stderr=result.stderr,
                )
            
            logger.info(f"[FFmpeg] 字幕添加成功: {output_video}")
            return output_video
        
        except subprocess.TimeoutExpired:
            raise RenderError("字幕添加超时（>5分钟）", step="add_subtitle")
    
    @retry(max_attempts=2, backoff_factor=2.0, exceptions=(subprocess.CalledProcessError,))
    @log_execution(log_level="info")
    def add_audio(
        self,
        input_video: Path,
        audio_file: Path,
        output_video: Path,
        loop_audio: bool = True,
        audio_volume: float = 0.3,
    ) -> Path:
        """
        添加背景音乐
        
        Args:
            input_video: 输入视频路径
            audio_file: 音频文件路径
            output_video: 输出视频路径
            loop_audio: 是否循环音乐
            audio_volume: 音乐音量（0.0-1.0）
        
        Returns:
            输出文件路径
        
        Raises:
            RenderError: 操作失败
        """
        if not input_video.exists():
            raise RenderError(f"输入视频不存在: {input_video}", step="add_audio")
        
        if not audio_file.exists():
            raise RenderError(f"音频文件不存在: {audio_file}", step="add_audio")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建 FFmpeg 命令
        cmd = [
            self.ffmpeg_path,
            "-i", str(input_video),
            "-i", str(audio_file),
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-filter:a", f"volume={audio_volume}",
            "-y",
            str(output_video),
        ]
        
        try:
            logger.debug(f"[FFmpeg] 命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise RenderError(
                    f"音频添加失败",
                    step="add_audio",
                    ffmpeg_stderr=result.stderr,
                )
            
            logger.info(f"[FFmpeg] 音频添加成功: {output_video}")
            return output_video
        
        except subprocess.TimeoutExpired:
            raise RenderError("音频添加超时（>5分钟）", step="add_audio")
    
    @retry(max_attempts=2, backoff_factor=2.0, exceptions=(subprocess.CalledProcessError,))
    @log_execution(log_level="info")
    def concatenate_videos(
        self,
        video_list: List[Path],
        output_video: Path,
        transition_duration: float = 0.5,
    ) -> Path:
        """
        拼接多个视频
        
        Args:
            video_list: 视频路径列表
            output_video: 输出视频路径
            transition_duration: 转场时长（秒，0 表示无转场）
        
        Returns:
            输出文件路径
        
        Raises:
            RenderError: 操作失败
        """
        if not video_list:
            raise RenderError("视频列表为空", step="concatenate_videos")
        
        for video in video_list:
            if not video.exists():
                raise RenderError(f"视频不存在: {video}", step="concatenate_videos")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建拼接文件列表
        concat_file = output_video.parent / "concat_list.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for video in video_list:
                f.write(f"file '{video.resolve()}'\n")
        
        try:
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-y",
                str(output_video),
            ]
            
            logger.debug(f"[FFmpeg] 命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise RenderError(
                    f"视频拼接失败",
                    step="concatenate_videos",
                    ffmpeg_stderr=result.stderr,
                )
            
            # 清理临时文件
            concat_file.unlink()
            
            logger.info(f"[FFmpeg] 视频拼接成功: {output_video}")
            return output_video
        
        except subprocess.TimeoutExpired:
            raise RenderError("视频拼接超时（>10分钟）", step="concatenate_videos")
    
    @retry(max_attempts=2, backoff_factor=2.0, exceptions=(subprocess.CalledProcessError,))
    @log_execution(log_level="info")
    def convert_format(
        self,
        input_video: Path,
        output_video: Path,
        target_format: str = "mp4",
        bitrate: int = 8000,
    ) -> Path:
        """
        转换视频格式
        
        Args:
            input_video: 输入视频路径
            output_video: 输出视频路径
            target_format: 目标格式（mp4/webm/mov）
            bitrate: 比特率（kbps）
        
        Returns:
            输出文件路径
        
        Raises:
            RenderError: 操作失败
        """
        if not input_video.exists():
            raise RenderError(f"输入视频不存在: {input_video}", step="convert_format")
        
        output_video.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据格式选择编码器
        codec_map = {
            "mp4": ("libx264", "aac"),
            "webm": ("libvpx-vp9", "libopus"),
            "mov": ("libx264", "aac"),
        }
        
        if target_format not in codec_map:
            raise RenderError(f"不支持的格式: {target_format}", step="convert_format")
        
        video_codec, audio_codec = codec_map[target_format]
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(input_video),
            "-c:v", video_codec,
            "-c:a", audio_codec,
            "-b:v", f"{bitrate}k",
            "-y",
            str(output_video),
        ]
        
        try:
            logger.debug(f"[FFmpeg] 命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise RenderError(
                    f"格式转换失败",
                    step="convert_format",
                    ffmpeg_stderr=result.stderr,
                )
            
            logger.info(f"[FFmpeg] 格式转换成功: {output_video}")
            return output_video
        
        except subprocess.TimeoutExpired:
            raise RenderError("格式转换超时（>10分钟）", step="convert_format")
    
    @log_execution(log_level="info")
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
        
        Returns:
            包含视频信息的字典
        
        Raises:
            RenderError: 无法获取信息
        """
        if not video_path.exists():
            raise RenderError(f"视频不存在: {video_path}", step="get_video_info")
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_path),
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            # 解析输出
            output = result.stderr
            info = {
                "path": str(video_path),
                "file_size": video_path.stat().st_size,
            }
            
            # 简单解析 duration
            for line in output.split('\n'):
                if 'Duration' in line:
                    # 从 "Duration: HH:MM:SS.ms" 提取时长
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    parts = duration_str.split(':')
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    info['duration'] = hours * 3600 + minutes * 60 + seconds
                
                if 'Video:' in line:
                    # 提取分辨率
                    if 'x' in line:
                        for token in line.split():
                            if 'x' in token and any(c.isdigit() for c in token):
                                try:
                                    w, h = token.split('x')
                                    if w.isdigit() and h.isdigit():
                                        info['resolution'] = token
                                        break
                                except:
                                    pass
            
            return info
        
        except subprocess.TimeoutExpired:
            raise RenderError("获取视频信息超时", step="get_video_info")
        except Exception as e:
            raise RenderError(f"解析视频信息失败: {str(e)}", step="get_video_info")


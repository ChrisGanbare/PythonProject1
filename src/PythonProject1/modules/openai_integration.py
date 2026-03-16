"""
OpenAI API 集成模块
用于生成视频文案、字幕等内容
"""

import logging
import json
from typing import Optional, Dict, Any, List

from config.settings import settings
from models.exceptions import APIError
from utils.decorators import retry, log_execution


logger = logging.getLogger(__name__)


class ContentWriter:
    """内容生成器（基于 OpenAI）"""
    
    def __init__(self):
        """初始化内容生成器"""
        self.api_key = settings.api.openai_api_key
        self.model = settings.api.openai_model
        self.timeout = settings.api.openai_timeout
        
        if not self.api_key:
            logger.warning("[ContentWriter] OpenAI API 密钥未配置，某些功能将不可用")
        else:
            try:
                import openai
                openai.api_key = self.api_key
                self.openai = openai
                logger.info(f"[ContentWriter] 初始化完成 | 模型: {self.model}")
            except ImportError:
                logger.warning("[ContentWriter] openai 库未安装，请执行: pip install openai")
                self.openai = None
    
    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(APIError,))
    @log_execution(log_level="info")
    def generate_script(
        self,
        topic: str,
        duration: int = 30,
        style: str = "educational",
        language: str = "zh",
    ) -> str:
        """
        生成视频脚本
        
        Args:
            topic: 视频主题
            duration: 视频时长（秒）
            style: 风格（educational/entertaining/commercial）
            language: 语言（zh/en）
        
        Returns:
            生成的脚本
        
        Raises:
            APIError: API 调用失败
        """
        if not self.openai:
            raise APIError(
                "OpenAI 库未初始化，无法生成脚本",
                api_name="OpenAI",
            )
        
        prompt = self._build_script_prompt(topic, duration, style, language)
        
        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频文案编写师，擅长为短视频创作高质量的脚本。"
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
                timeout=self.timeout,
            )
            
            script = response.choices[0].message.content
            logger.info(f"[OpenAI] 脚本生成成功 | 主题: {topic}")
            return script
        
        except Exception as e:
            raise APIError(
                f"脚本生成失败: {str(e)}",
                api_name="OpenAI",
            )
    
    @retry(max_attempts=3, backoff_factor=2.0, exceptions=(APIError,))
    @log_execution(log_level="info")
    def generate_subtitles(
        self,
        text: str,
        duration: int = 30,
        language: str = "zh",
        max_chars_per_line: int = 12,
    ) -> List[Dict[str, Any]]:
        """
        生成字幕（SRT 格式数据）
        
        Args:
            text: 原始文本
            duration: 视频时长（秒）
            language: 语言
            max_chars_per_line: 每行最大字符数
        
        Returns:
            字幕数据列表，每项包含: {
                'index': int,
                'start': str (HH:MM:SS,mmm),
                'end': str (HH:MM:SS,mmm),
                'text': str,
            }
        
        Raises:
            APIError: API 调用失败
        """
        if not self.openai:
            raise APIError(
                "OpenAI 库未初始化，无法生成字幕",
                api_name="OpenAI",
            )
        
        prompt = f"""将以下文本转换为视频字幕（JSON 格式）。
要求：
1. 每条字幕不超过 {max_chars_per_line} 个字符
2. 时间均匀分布在 0-{duration} 秒内
3. 字幕要自然切分，不要硬生生断句

原始文本：
{text}

返回 JSON 格式：
[
  {{
    "index": 1,
    "start_ms": 0,
    "end_ms": 3000,
    "text": "字幕文本"
  }},
  ...
]

只返回 JSON 数据，不需要其他说明。"""
        
        try:
            response = self.openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的字幕制作专家，能精准地将文本转换为分节点的字幕。"
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.5,
                timeout=self.timeout,
            )
            
            response_text = response.choices[0].message.content
            
            # 解析 JSON
            try:
                # 尝试找到 JSON 部分
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    subtitles_data = json.loads(json_str)
                else:
                    raise ValueError("响应中未找到 JSON 格式")
                
                # 转换为 SRT 格式
                subtitles = []
                for item in subtitles_data:
                    start_ms = item.get('start_ms', 0)
                    end_ms = item.get('end_ms', duration * 1000)
                    
                    subtitles.append({
                        'index': item.get('index', len(subtitles) + 1),
                        'start': self._ms_to_srt_time(start_ms),
                        'end': self._ms_to_srt_time(end_ms),
                        'text': item.get('text', ''),
                    })
                
                logger.info(f"[OpenAI] 字幕生成成功 | 共 {len(subtitles)} 条字幕")
                return subtitles
            
            except json.JSONDecodeError as e:
                raise APIError(
                    f"字幕 JSON 解析失败: {str(e)}",
                    api_name="OpenAI",
                )
        
        except Exception as e:
            raise APIError(
                f"字幕生成失败: {str(e)}",
                api_name="OpenAI",
            )
    
    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """将毫秒转换为 SRT 时间格式 HH:MM:SS,mmm"""
        total_seconds = ms // 1000
        milliseconds = ms % 1000
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    @staticmethod
    def _build_script_prompt(
        topic: str,
        duration: int,
        style: str,
        language: str,
    ) -> str:
        """构建脚本生成 Prompt"""
        style_desc = {
            "educational": "教育性、信息丰富、逻辑清晰",
            "entertaining": "娱乐性、幽默、吸引眼球",
            "commercial": "商业性、说服力强、呼吁行动",
        }.get(style, "教育性")
        
        lang_hint = "中文" if language == "zh" else "English"
        
        return f"""请为一个 {duration} 秒的短视频编写脚本。

主题：{topic}
风格：{style_desc}
语言：{lang_hint}

要求：
1. 开场要吸引注意力
2. 内容紧凑、信息密集
3. 有明确的结尾或呼吁
4. 适合配合视觉效果呈现
5. 避免过于复杂的语言

请提供脚本内容，并标注主要场景转换点。"""


def create_subtitle_file(
    subtitles: List[Dict[str, str]],
    output_path: str,
    format: str = "srt",
) -> None:
    """
    创建字幕文件
    
    Args:
        subtitles: 字幕数据列表
        output_path: 输出文件路径
        format: 格式（srt/vtt）
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        if format == "srt":
            for item in subtitles:
                f.write(f"{item['index']}\n")
                f.write(f"{item['start']} --> {item['end']}\n")
                f.write(f"{item['text']}\n")
                f.write("\n")
        
        elif format == "vtt":
            f.write("WEBVTT\n\n")
            for item in subtitles:
                # VTT 时间格式：HH:MM:SS.mmm
                start = item['start'].replace(',', '.')
                end = item['end'].replace(',', '.')
                f.write(f"{start} --> {end}\n")
                f.write(f"{item['text']}\n")
                f.write("\n")
    
    logger.info(f"[字幕] 文件已保存: {output_path}")


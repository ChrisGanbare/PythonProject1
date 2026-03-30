"""内容规划数据模型。"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ContentStyle(str, Enum):
    """统一内容风格。"""

    MINIMAL = "minimal"
    TECH = "tech"
    NEWS = "news"
    TRENDY = "trendy"


class ContentVariant(str, Enum):
    """内容结构版本。"""

    SHORT = "short"
    STANDARD = "standard"


class StoryBeatType(str, Enum):
    """短视频叙事节拍类型。"""

    HOOK = "hook"
    SETUP = "setup"
    CLIMAX = "climax"
    CONCLUSION = "conclusion"


class StoryBeat(BaseModel):
    """单个内容节拍。"""

    beat_type: StoryBeatType
    headline: str = Field(description="该段的标题提示")
    narration: str = Field(description="该段主字幕/旁白文案")
    visual_hint: str | None = Field(default=None, description="该段建议的视觉重点")
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)


class SubtitleCue(BaseModel):
    """字幕轨道中的单个 cue。"""

    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(gt=0.0)
    text: str
    beat_type: StoryBeatType
    style_token: str


class ConclusionCard(BaseModel):
    """结论卡片模板信息。"""

    title: str
    body: str
    accent_label: str
    theme: str


class ContentBrief(BaseModel):
    """业务层提供给公共内容规划器的最小输入。"""

    topic: str
    platform: str
    style: ContentStyle = ContentStyle.TECH
    variant: ContentVariant | None = None
    total_duration: int = Field(ge=1)
    hook_fact: str
    setup_fact: str
    climax_fact: str
    conclusion_fact: str
    call_to_action: str | None = None
    tags: list[str] = Field(default_factory=list)


class ContentPlan(BaseModel):
    """可直接用于预览、字幕和脚本生成的内容方案。"""

    topic: str
    platform: str
    style: ContentStyle
    variant: ContentVariant
    total_duration: int
    hook: str
    summary: str
    beats: list[StoryBeat]
    subtitle_cues: list[SubtitleCue] = Field(default_factory=list)
    conclusion_card: ConclusionCard
    tags: list[str] = Field(default_factory=list)

    def to_subtitle_items(self) -> list[dict[str, float | str]]:
        """转换为 SRT 写入所需的字幕切片。"""
        if self.subtitle_cues:
            return [
                {
                    "start": cue.start_seconds,
                    "end": cue.end_seconds,
                    "text": cue.text,
                    "style_token": cue.style_token,
                    "beat_type": cue.beat_type.value,
                }
                for cue in self.subtitle_cues
            ]
        return [
            {
                "start": beat.start_seconds,
                "end": beat.end_seconds,
                "text": beat.narration,
            }
            for beat in self.beats
        ]


"""内容模板库。"""

from __future__ import annotations

from shared.ai.content.schemas import ContentStyle, ContentVariant, StoryBeatType


STYLE_HEADLINES: dict[ContentStyle, dict[StoryBeatType, str]] = {
    ContentStyle.MINIMAL: {
        StoryBeatType.HOOK: "先看结论",
        StoryBeatType.SETUP: "核心对比",
        StoryBeatType.CLIMAX: "差距放大",
        StoryBeatType.CONCLUSION: "怎么选更好",
    },
    ContentStyle.TECH: {
        StoryBeatType.HOOK: "关键变量拉满",
        StoryBeatType.SETUP: "数据开始分叉",
        StoryBeatType.CLIMAX: "差距进入高潮",
        StoryBeatType.CONCLUSION: "最终策略判断",
    },
    ContentStyle.NEWS: {
        StoryBeatType.HOOK: "最新对比",
        StoryBeatType.SETUP: "数据复盘",
        StoryBeatType.CLIMAX: "重点数字",
        StoryBeatType.CONCLUSION: "结论提示",
    },
    ContentStyle.TRENDY: {
        StoryBeatType.HOOK: "别眨眼",
        StoryBeatType.SETUP: "往下看差距",
        StoryBeatType.CLIMAX: "真正离谱的来了",
        StoryBeatType.CONCLUSION: "一句话收尾",
    },
}


NARRATION_WRAPPERS: dict[ContentStyle, dict[StoryBeatType, str]] = {
    ContentStyle.MINIMAL: {
        StoryBeatType.HOOK: "{fact}",
        StoryBeatType.SETUP: "{fact}",
        StoryBeatType.CLIMAX: "{fact}",
        StoryBeatType.CONCLUSION: "{fact}",
    },
    ContentStyle.TECH: {
        StoryBeatType.HOOK: "把问题说透：{fact}",
        StoryBeatType.SETUP: "关键数据正在拉开：{fact}",
        StoryBeatType.CLIMAX: "真正需要记住的是：{fact}",
        StoryBeatType.CONCLUSION: "策略建议：{fact}",
    },
    ContentStyle.NEWS: {
        StoryBeatType.HOOK: "本期关注：{fact}",
        StoryBeatType.SETUP: "数据显示：{fact}",
        StoryBeatType.CLIMAX: "值得注意的是：{fact}",
        StoryBeatType.CONCLUSION: "最终结论：{fact}",
    },
    ContentStyle.TRENDY: {
        StoryBeatType.HOOK: "先别划走，{fact}",
        StoryBeatType.SETUP: "越往后看越明显：{fact}",
        StoryBeatType.CLIMAX: "最炸裂的一幕是：{fact}",
        StoryBeatType.CONCLUSION: "一句话记住：{fact}",
    },
}


PLATFORM_HOOKS: dict[str, dict[ContentStyle, str]] = {
    "douyin": {
        ContentStyle.MINIMAL: "先看最关键的一句：{fact}",
        ContentStyle.TECH: "先把结论砸出来：{fact}",
        ContentStyle.NEWS: "今天先看这组关键数据：{fact}",
        ContentStyle.TRENDY: "别划走，最狠的点先告诉你：{fact}",
    },
    "xiaohongshu": {
        ContentStyle.MINIMAL: "做决策前先看：{fact}",
        ContentStyle.TECH: "这组数据真的值得收藏：{fact}",
        ContentStyle.NEWS: "把重点先讲清楚：{fact}",
        ContentStyle.TRENDY: "你以为差不多？其实{fact}",
    },
    "bilibili_vertical": {
        ContentStyle.MINIMAL: "开头先看核心问题：{fact}",
        ContentStyle.TECH: "先把变量摆上桌：{fact}",
        ContentStyle.NEWS: "本期复盘一个关键结论：{fact}",
        ContentStyle.TRENDY: "这组对比真有点离谱：{fact}",
    },
    "bilibili_landscape": {
        ContentStyle.MINIMAL: "先建立问题背景：{fact}",
        ContentStyle.TECH: "先看核心变量如何影响结果：{fact}",
        ContentStyle.NEWS: "先交代今天的主题：{fact}",
        ContentStyle.TRENDY: "先把最有冲击的一幕放出来：{fact}",
    },
}


CONCLUSION_CARD_THEMES: dict[ContentStyle, dict[str, str]] = {
    ContentStyle.MINIMAL: {"title": "一页结论", "theme": "clean-slate"},
    ContentStyle.TECH: {"title": "最终策略判断", "theme": "tech-blue"},
    ContentStyle.NEWS: {"title": "重点结论", "theme": "news-red"},
    ContentStyle.TRENDY: {"title": "一句话记住", "theme": "neon-pop"},
}


VARIANT_VISUAL_HINTS: dict[ContentVariant, dict[StoryBeatType, str]] = {
    ContentVariant.SHORT: {
        StoryBeatType.HOOK: "大字数字冲击 + 快速入场",
        StoryBeatType.SETUP: "只保留一组核心对比图",
        StoryBeatType.CLIMAX: "放大差额数字与趋势拐点",
        StoryBeatType.CONCLUSION: "强结论卡片 + CTA",
    },
    ContentVariant.STANDARD: {
        StoryBeatType.HOOK: "建立问题和冲突",
        StoryBeatType.SETUP: "完整展示关键比较过程",
        StoryBeatType.CLIMAX: "强化关键节点与累计差距",
        StoryBeatType.CONCLUSION: "结论卡片 + 选择建议",
    },
}



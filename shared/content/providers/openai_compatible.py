"""OpenAI-compatible screenplay provider."""

from __future__ import annotations

import json
from typing import Any

import requests

from shared.content.providers.base import ProviderDescriptor, ScreenplayProvider
from shared.content.screenplay import Screenplay


class OpenAICompatibleScreenplayProvider(ScreenplayProvider):
    descriptor = ProviderDescriptor(
        name="openai_compatible",
        description="Remote screenplay provider using OpenAI-compatible chat completions APIs.",
        supports_remote=True,
    )

    def __init__(self, *, base_url: str | None, api_key: str | None, model: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def _ensure_configured(self) -> None:
        if not self.base_url or not self.api_key:
            raise RuntimeError("openai_compatible provider is not configured")

    def generate(
        self,
        *,
        topic: str,
        style: str,
        target_audience: str,
        platform: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Screenplay:
        self._ensure_configured()
        
        schema_json = json.dumps(Screenplay.model_json_schema(), ensure_ascii=False)
        system_prompt = (
            "你是一名专为中文自媒体创作者服务的数据可视化短视频编剧。"
            "请严格输出符合以下 JSON Schema 定义的 Screenplay 结构。\n"
            f"Schema: {schema_json}\n"
            "确保 'scenes' 列表中包含具体的由 'narration' 和 'visuals' 组成的场景描述。"
        )

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "topic": topic,
                            "style": style,
                            "target_audience": target_audience,
                            "platform": platform,
                            "context": context or {},
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        response = requests.post(
            self.base_url.rstrip("/") + "/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        screenplay_dict = json.loads(content)
        return Screenplay.model_validate(screenplay_dict)


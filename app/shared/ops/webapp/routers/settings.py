"""全局设置与 OpenAI 校验 API。"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.ops.webapp.env_settings import mask_secret, update_env_file

logger = logging.getLogger("dashboard")

try:
    import openai
except ImportError:
    openai = None


class SettingsResponse(BaseModel):
    """Secure settings model for frontend consumption."""

    video_width: int
    video_height: int
    video_fps: int
    video_total_duration: int

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str
    pexels_api_key: str | None = None

    screenplay_provider_default: str
    output_dir: str | None = None
    api_key_configured: bool = False


class SettingsUpdateRequest(BaseModel):
    """Payload for updating settings."""

    video_width: int | None = None
    video_height: int | None = None
    video_fps: int | None = None
    video_total_duration: int | None = None

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    pexels_api_key: str | None = None

    screenplay_provider_default: str | None = None
    output_dir: str | None = None


class ValidateOpenAIRequest(BaseModel):
    api_key: str
    base_url: str | None = None
    model_hint: str | None = None


router = APIRouter()


@router.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get global settings with masked secrets."""
    from shared.ops.config.settings import settings

    return SettingsResponse(
        video_width=settings.video.width,
        video_height=settings.video.height,
        video_fps=settings.video.fps,
        video_total_duration=settings.video.total_duration,
        openai_api_key=mask_secret(settings.api.openai_compatible_api_key),
        openai_base_url=settings.api.openai_compatible_base_url,
        openai_model=settings.api.openai_compatible_model,
        pexels_api_key=mask_secret(settings.api.pexels_api_key),
        screenplay_provider_default=settings.api.screenplay_provider_default,
        output_dir=str(settings.video.output_dir),
        api_key_configured=bool(settings.api.openai_compatible_api_key),
    )


@router.get("/api/settings/reveal-keys")
async def reveal_keys():
    """Return unmasked API keys for local display. Localhost-only tool."""
    from shared.ops.config.settings import settings

    return {
        "openai_api_key": settings.api.openai_compatible_api_key or "",
        "pexels_api_key": settings.api.pexels_api_key or "",
    }


@router.put("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    """Update global settings and persist to .env."""
    from shared.ops.config.settings import settings

    updates = {}

    if request.video_width is not None:
        settings.video.width = request.video_width
        updates["video_width"] = request.video_width
    if request.video_height is not None:
        settings.video.height = request.video_height
        updates["video_height"] = request.video_height
    if request.video_fps is not None:
        settings.video.fps = request.video_fps
        updates["video_fps"] = request.video_fps
    if request.video_total_duration is not None:
        settings.video.total_duration = request.video_total_duration
        updates["video_total_duration"] = request.video_total_duration

    if request.openai_api_key and "..." not in request.openai_api_key:
        settings.api.openai_compatible_api_key = request.openai_api_key
        updates["openai_api_key"] = request.openai_api_key

    if request.openai_base_url and "..." not in request.openai_base_url:
        settings.api.openai_compatible_base_url = request.openai_base_url
        updates["openai_base_url"] = request.openai_base_url

    if request.openai_model:
        settings.api.openai_compatible_model = request.openai_model
        updates["openai_model"] = request.openai_model

    if request.pexels_api_key and "..." not in request.pexels_api_key:
        settings.api.pexels_api_key = request.pexels_api_key
        updates["pexels_api_key"] = request.pexels_api_key

    if request.screenplay_provider_default:
        settings.api.screenplay_provider_default = request.screenplay_provider_default
        updates["screenplay_provider_default"] = request.screenplay_provider_default

    if request.output_dir:
        from pathlib import Path
        p = Path(request.output_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        if not os.access(p, os.W_OK):
            raise HTTPException(status_code=400, detail=f"路径不可写：{p}")
        settings.video.output_dir = p
        updates["output_dir"] = str(p)

    try:
        update_env_file(updates)
    except Exception as e:
        logger.error("Failed to persist settings to .env: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"配置已更新至内存，但写入 .env 文件失败：{e}",
        ) from e

    return {"status": "success", "message": "Settings updated", "updated_keys": list(updates.keys())}


@router.post("/api/settings/validate-openai")
async def validate_openai(request: ValidateOpenAIRequest):
    """Validate OpenAI API Key and list available models."""
    if not openai:
        return {
            "valid": False,
            "error": "OpenAI library not installed on server",
        }

    api_key = request.api_key
    base_url = request.base_url

    if base_url:
        base_url = base_url.strip()
        if base_url.endswith("/"):
            base_url = base_url[:-1]

    try:
        from shared.ops.config.settings import settings

        stored_key = settings.api.openai_compatible_api_key

        if api_key.startswith("sk-") and "..." in api_key and stored_key:
            if len(api_key) > 7 and stored_key.startswith(api_key[:3]) and stored_key.endswith(api_key[-4:]):
                api_key = stored_key

        stored_url = settings.api.openai_compatible_base_url
        if base_url and "..." in base_url and stored_url:
            if len(base_url) > 7 and stored_url.startswith(base_url[:3]) and stored_url.endswith(base_url[-4:]):
                base_url = stored_url

        logger.info("Validating OpenAI connection. Base URL: %s", base_url or "Default (Official)")

        client_kwargs = {"api_key": api_key, "timeout": 10.0}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = openai.OpenAI(**client_kwargs)

        models: list[str] = []
        try:
            logger.info("Attempting to list models...")
            response = client.models.list()
            models = sorted([m.id for m in response.data])
            logger.info("Successfully listed models: %d found", len(models))
        except Exception as list_err:
            err_str = str(list_err)
            is_404 = "404" in err_str or (
                hasattr(list_err, "status_code") and list_err.status_code == 404
            )
            logger.warning("Failed to list models: %s", list_err)

            test_model = (request.model_hint or "").strip()
            if test_model:
                try:
                    client.chat.completions.create(
                        model=test_model,
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=1,
                    )
                    logger.info("Fallback generation successful with model '%s'", test_model)
                    models = [test_model]
                except Exception as gen_err:
                    logger.error("Fallback generation also failed: %s", gen_err)
                    gen_str = str(gen_err)
                    is_model_404 = "404" in gen_str or (
                        hasattr(gen_err, "status_code") and gen_err.status_code == 404
                    )
                    if is_model_404:
                        friendly = (
                            f"模型 '{test_model}' 不存在或名称有误，请在模型名称字段填写正确的 Model ID 后重试。"
                            f"（如使用 DashScope，可填写 qwen-turbo / qwen-plus / qwen-max 等）"
                        )
                    else:
                        friendly = f"接口验证失败：{gen_str}"
                    return {
                        "valid": False,
                        "error": friendly,
                        "details": f"List Models: {list_err}; Generation Check: {gen_err}",
                    }
            else:
                if is_404:
                    logger.info("Provider returned 404 on /models; returning valid=True with empty list.")
                    models = []
                else:
                    return {
                        "valid": False,
                        "error": f"获取模型列表失败：{err_str}（请填写模型名称后再试）",
                        "details": err_str,
                    }

        return {
            "valid": True,
            "message": "Connection successful",
            "models": models,
        }
    except Exception as e:
        logger.warning("OpenAI validation failed: %s", str(e))
        msg = str(e)
        if "404" in msg:
            model_hint = (request.model_hint or "").strip()
            if model_hint:
                return {
                    "valid": False,
                    "error": (
                        f"模型 '{model_hint}' 不存在或名称有误，请在模型名称字段填写正确的 Model ID 后重试。"
                        "（如使用 DashScope，可填写 qwen-turbo / qwen-plus / qwen-max 等）"
                    ),
                }
            return {"valid": False, "error": "接口地址不支持该操作（404），请检查 Base URL 是否正确。"}
        if "timeout" in msg.lower() and (not request.base_url or not request.base_url.strip()):
            msg = "请求超时——是否忘记填写 Base URL？"
        elif "connection" in msg.lower() or "connect" in msg.lower():
            msg = f"无法连接至 {request.base_url}，请检查地址和网络。"
        return {
            "valid": False,
            "error": msg,
        }

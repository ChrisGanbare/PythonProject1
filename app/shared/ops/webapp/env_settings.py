"""设置与 .env 读写（供 settings 路由使用）。"""

from __future__ import annotations

import contextlib
import os
import tempfile
from typing import Any

from shared.ops.webapp.state import REPO_ROOT


def mask_secret(value: str | None) -> str | None:
    if not value or len(value) < 8:
        return None
    return f"{value[:3]}...{value[-4:]}"


def update_env_file(updates: dict[str, Any]) -> None:
    env_path = REPO_ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    key_map = {
        "video_width": "VIDEO__WIDTH",
        "video_height": "VIDEO__HEIGHT",
        "video_fps": "VIDEO__FPS",
        "video_total_duration": "VIDEO__TOTAL_DURATION",
        "openai_api_key": "API__OPENAI_COMPATIBLE_API_KEY",
        "openai_base_url": "API__OPENAI_COMPATIBLE_BASE_URL",
        "openai_model": "API__OPENAI_COMPATIBLE_MODEL",
        "pexels_api_key": "API__PEXELS_API_KEY",
        "screenplay_provider_default": "API__SCREENPLAY_PROVIDER_DEFAULT",
    }

    new_lines: list[str] = []
    seen_keys: set[str] = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            field = next((f for f, k in key_map.items() if k == key), None)
            if field and field in updates and updates[field] is not None:
                new_lines.append(f"{key}={updates[field]}")
                seen_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    for field, value in updates.items():
        env_key = key_map.get(field)
        if env_key and env_key not in seen_keys and value is not None:
            new_lines.append(f"{env_key}={value}")

    tmp_fd, tmp_path = tempfile.mkstemp(dir=env_path.parent, prefix=".env.tmp.")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
        os.replace(tmp_path, env_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")

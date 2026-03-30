"""P3: suggested directories for frame-level cache (opt-in; caller creates dirs)."""

from __future__ import annotations

import re
from pathlib import Path

from shared.ops.config.settings import settings


def sanitize_cache_segment(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_").lower()
    return s or "default"


def render_cache_dir(project: str, fingerprint_hex: str) -> Path:
    """
    Subdirectory under runtime cache for a render identity.

    `fingerprint_hex` should match `reproducibility_fingerprint` / `VIDEO_RENDER_FINGERPRINT`
    (use first 32 chars if full 64 is too long for paths).
    """
    seg = sanitize_cache_segment(project)
    fp = fingerprint_hex.strip().lower()[:32]
    return settings.cache_dir / "renders" / seg / fp

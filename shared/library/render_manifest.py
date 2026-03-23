"""Sidecar manifest for reproducibility: links outputs to script version and assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from shared.content.screenplay import Screenplay

MANIFEST_SCHEMA_VERSION = 2

_VIDEO_KEYS_FOR_FINGERPRINT = (
    "width",
    "height",
    "fps",
    "total_duration",
    "dpi",
    "bitrate",
    "crf",
    "preset",
    "renderer_revision",
)


def collect_viz_scene_refs_from_screenplay(screenplay: Screenplay) -> list[dict[str, Any]]:
    """Extract per-scene viz binding from `Scene.action_directives` (see screenplay schema)."""
    refs: list[dict[str, Any]] = []
    for scene in screenplay.scenes:
        ad = scene.action_directives or {}
        refs.append(
            {
                "scene_id": scene.id,
                "viz_scene_id": ad.get("viz_scene_id"),
                "chart_type": ad.get("chart_type"),
                "reference_style": ad.get("reference_style"),
            }
        )
    return refs


def _sha256_stable(stable: dict[str, Any]) -> str:
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compute_reproducibility_fingerprint(
    *,
    loan: dict[str, Any] | None,
    video_config: dict[str, Any],
    viz_refs: list[dict[str, Any]],
) -> str:
    """Stable hash for same data + render knobs + viz scene bindings (audit / cache identity)."""
    video_slice = {k: video_config.get(k) for k in _VIDEO_KEYS_FOR_FINGERPRINT}
    stable = {
        "loan": loan or {},
        "video": video_slice,
        "viz_refs": viz_refs,
    }
    return _sha256_stable(stable)


def compute_fund_reproducibility_fingerprint(
    *,
    fund: dict[str, Any],
    video_config: dict[str, Any],
) -> str:
    """基金子项目成片身份（与贷款指纹结构独立，避免域混淆）。"""
    video_slice = {k: video_config.get(k) for k in _VIDEO_KEYS_FOR_FINGERPRINT}
    stable = {
        "domain": "fund_fee_erosion",
        "fund": fund,
        "video": video_slice,
    }
    return _sha256_stable(stable)


def collect_asset_ids_from_screenplay(screenplay: Screenplay) -> list[str]:
    """Collect referenced asset ids from audio cues and visual style hints."""
    found: set[str] = set()
    for scene in screenplay.scenes:
        for cue in scene.audio_cues:
            if cue.asset_id:
                found.add(cue.asset_id)
        for visual in scene.visuals:
            aid = visual.style.get("asset_id") if isinstance(visual.style, dict) else None
            if isinstance(aid, str) and aid:
                found.add(aid)
    return sorted(found)


def build_render_manifest_payload(
    *,
    task_id: str,
    final_video: Path,
    platform: str,
    quality: str | None,
    video_config: dict[str, Any],
    loan: dict[str, Any] | None = None,
    script_id: str | None = None,
    script_version: int | None = None,
    script_status: str | None = None,
    screenplay: Screenplay | None = None,
    scene_schedule: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
    viz_backend_default: str = "matplotlib",
) -> dict[str, Any]:
    asset_ids: list[str] = []
    if screenplay is not None:
        asset_ids = collect_asset_ids_from_screenplay(screenplay)

    viz_refs = collect_viz_scene_refs_from_screenplay(screenplay) if screenplay is not None else []
    repro_fp = compute_reproducibility_fingerprint(
        loan=loan,
        video_config=video_config,
        viz_refs=viz_refs,
    )

    payload: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "task_id": task_id,
        "platform": platform,
        "quality": quality,
        "render": video_config,
        "output": {"final_video": str(final_video.resolve())},
        "script": None,
        "loan": loan,
        "asset_ids": asset_ids,
        "scene_schedule": scene_schedule,
        "viz": {
            "default_backend": viz_backend_default,
            "scene_refs": viz_refs,
            "reproducibility_fingerprint": repro_fp,
        },
    }
    if script_id is not None:
        payload["script"] = {
            "script_id": script_id,
            "version": script_version,
            "status": script_status,
            "screenplay_title": screenplay.title if screenplay else None,
        }
    if extra:
        payload["extra"] = extra
    return payload


def build_fund_render_manifest_payload(
    *,
    task_id: str,
    final_video: Path,
    platform: str,
    quality: str | None,
    video_config: dict[str, Any],
    fund: dict[str, Any],
    viz_backend_default: str = "matplotlib",
) -> dict[str, Any]:
    """Sidecar payload for fund_fee_erosion API (no screenplay / loan keys)."""
    repro_fp = compute_fund_reproducibility_fingerprint(fund=fund, video_config=video_config)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "project": "fund_fee_erosion",
        "task_id": task_id,
        "platform": platform,
        "quality": quality,
        "render": video_config,
        "output": {"final_video": str(final_video.resolve())},
        "fund": fund,
        "asset_ids": [],
        "scene_schedule": None,
        "viz": {
            "default_backend": viz_backend_default,
            "scene_refs": [],
            "reproducibility_fingerprint": repro_fp,
        },
    }


def write_render_manifest(manifest_path: Path, payload: dict[str, Any]) -> Path:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path

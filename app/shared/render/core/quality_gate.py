"""Standardized quality gate: pre-render contract + post-render validation.

Every project renderer should call:
  1. ``validate_render_inputs()`` before rendering (fail-fast on bad config)
  2. ``validate_video_output()`` after rendering (reject non-conforming output)

This ensures ALL projects produce videos that meet platform specs regardless of
which renderer backend they use.
"""

from __future__ import annotations

import json
import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.ops.config.settings import QUALITY_PRESETS, get_quality_preset
from shared.output.platform.presets import ALL_PRESETS, PlatformPreset, get_platform_preset


# ── Tolerances ────────────────────────────────────────────────────────────────
_RESOLUTION_TOLERANCE_PX = 2      # allow ±2px for rounding
_FPS_TOLERANCE = 0.5              # allow ±0.5 fps for VFR streams
_DURATION_TOLERANCE_SEC = 1.0     # allow ±1s for encoding padding


@dataclass(frozen=True)
class RenderContract:
    """Pre-validated render specification. Pass this to your renderer."""

    platform: str
    quality: str
    width: int
    height: int
    fps: int
    dpi: int
    bitrate: int
    crf: int
    preset: str
    safe_top: int
    safe_bottom: int
    safe_left: int
    safe_right: int
    expected_duration: float | None = None

    def to_env_dict(self) -> dict[str, str]:
        """Export as environment variables for subprocess-based renderers."""
        return {
            "VIDEO_WIDTH": str(self.width),
            "VIDEO_HEIGHT": str(self.height),
            "VIDEO_FPS": str(self.fps),
            "VIDEO_DPI": str(self.dpi),
            "VIDEO_BITRATE": str(self.bitrate),
            "VIDEO_CRF": str(self.crf),
            "VIDEO_PRESET": self.preset,
            "VIDEO_PLATFORM": self.platform,
            "VIDEO_QUALITY": self.quality,
            "VIDEO_SAFE_TOP": str(self.safe_top),
            "VIDEO_SAFE_BOTTOM": str(self.safe_bottom),
            "VIDEO_SAFE_LEFT": str(self.safe_left),
            "VIDEO_SAFE_RIGHT": str(self.safe_right),
        }

    def to_dict(self) -> dict[str, Any]:
        """Export as plain dict for fingerprinting / manifest use."""
        return {
            "platform": self.platform,
            "quality": self.quality,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "dpi": self.dpi,
            "bitrate": self.bitrate,
            "crf": self.crf,
            "preset": self.preset,
            "safe_top": self.safe_top,
            "safe_bottom": self.safe_bottom,
            "safe_left": self.safe_left,
            "safe_right": self.safe_right,
        }


@dataclass
class QualityViolation:
    field: str
    expected: Any
    actual: Any
    severity: str = "error"   # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: expected {self.expected}, got {self.actual}"


@dataclass
class QualityReport:
    passed: bool
    violations: list[QualityViolation] = field(default_factory=list)
    video_path: Path | None = None
    contract: RenderContract | None = None

    def summary(self) -> str:
        if self.passed:
            return "✓ Quality gate passed"
        lines = ["✗ Quality gate FAILED:"]
        for v in self.violations:
            lines.append(f"  {v}")
        return "\n".join(lines)


# ── Pre-render: build validated contract ──────────────────────────────────────

def validate_render_inputs(
    *,
    platform: str,
    quality: str,
    expected_duration: float | None = None,
) -> RenderContract:
    """Build a ``RenderContract`` from platform + quality names.

    Raises ``ValueError`` if platform or quality is unknown.
    This is the ONLY place where platform × quality → concrete numbers mapping
    should happen. Individual projects must NOT duplicate this logic.
    """
    pp = get_platform_preset(platform)
    qp = get_quality_preset(quality)

    return RenderContract(
        platform=platform,
        quality=quality,
        width=pp.width,
        height=pp.height,
        fps=pp.fps,
        dpi=int(qp["dpi"]),
        bitrate=int(qp["bitrate"]),
        crf=int(qp["crf"]),
        preset=str(qp["preset"]),
        safe_top=pp.safe_top,
        safe_bottom=pp.safe_bottom,
        safe_left=pp.safe_left,
        safe_right=pp.safe_right,
        expected_duration=expected_duration,
    )


# ── Post-render: validate output video ────────────────────────────────────────

def _probe_video(video_path: Path) -> dict[str, Any] | None:
    """Use ffprobe to extract video stream metadata."""
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    cmd = [
        ffprobe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def validate_video_output(
    video_path: Path,
    contract: RenderContract,
) -> QualityReport:
    """Check that a rendered video conforms to its ``RenderContract``.

    Returns a ``QualityReport`` with pass/fail and detailed violations.
    """
    violations: list[QualityViolation] = []

    if not video_path.exists():
        violations.append(QualityViolation("file", "exists", "missing"))
        return QualityReport(passed=False, violations=violations, video_path=video_path, contract=contract)

    if video_path.stat().st_size == 0:
        violations.append(QualityViolation("file_size", "> 0 bytes", "0 bytes"))
        return QualityReport(passed=False, violations=violations, video_path=video_path, contract=contract)

    probe = _probe_video(video_path)
    if probe is None:
        violations.append(QualityViolation("ffprobe", "readable", "probe failed", severity="warning"))
        return QualityReport(passed=True, violations=violations, video_path=video_path, contract=contract)

    # Find video stream
    video_stream = None
    for s in probe.get("streams", []):
        if s.get("codec_type") == "video":
            video_stream = s
            break

    if video_stream is None:
        violations.append(QualityViolation("video_stream", "present", "no video stream"))
        return QualityReport(passed=False, violations=violations, video_path=video_path, contract=contract)

    # Resolution check
    actual_w = int(video_stream.get("width", 0))
    actual_h = int(video_stream.get("height", 0))
    if abs(actual_w - contract.width) > _RESOLUTION_TOLERANCE_PX:
        violations.append(QualityViolation("width", contract.width, actual_w))
    if abs(actual_h - contract.height) > _RESOLUTION_TOLERANCE_PX:
        violations.append(QualityViolation("height", contract.height, actual_h))

    # FPS check
    fps_str = video_stream.get("r_frame_rate", "0/1")
    try:
        num, den = fps_str.split("/")
        actual_fps = float(num) / float(den) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        actual_fps = 0.0
    if abs(actual_fps - contract.fps) > _FPS_TOLERANCE:
        violations.append(QualityViolation("fps", contract.fps, round(actual_fps, 2)))

    # Codec check
    actual_codec = video_stream.get("codec_name", "")
    if actual_codec not in ("h264", "hevc"):
        violations.append(QualityViolation("codec", "h264/hevc", actual_codec, severity="warning"))

    # Pixel format check
    actual_pix = video_stream.get("pix_fmt", "")
    if actual_pix != "yuv420p":
        violations.append(QualityViolation("pix_fmt", "yuv420p", actual_pix, severity="warning"))

    # Duration check (if expected)
    if contract.expected_duration is not None:
        fmt = probe.get("format", {})
        actual_dur = float(fmt.get("duration", 0))
        if abs(actual_dur - contract.expected_duration) > _DURATION_TOLERANCE_SEC:
            violations.append(QualityViolation(
                "duration",
                f"{contract.expected_duration}s ± {_DURATION_TOLERANCE_SEC}s",
                f"{actual_dur:.1f}s",
            ))

    has_errors = any(v.severity == "error" for v in violations)
    return QualityReport(
        passed=not has_errors,
        violations=violations,
        video_path=video_path,
        contract=contract,
    )


# ── Convenience: all-in-one for simple renderers ──────────────────────────────

def require_quality_pass(video_path: Path, contract: RenderContract) -> Path:
    """Validate and raise if quality gate fails. Returns path on success."""
    report = validate_video_output(video_path, contract)
    if not report.passed:
        raise RuntimeError(f"Quality gate failed for {video_path}:\n{report.summary()}")
    return video_path

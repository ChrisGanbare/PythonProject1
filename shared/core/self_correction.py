"""
Self-Correction feedback loop for render pipelines.

Captures subprocess render errors, classifies them, applies automated fixes,
and retries — reducing the need for human intervention in the
``data → code → render → compose`` pipeline.

Architecture
------------
                   ┌──────────────┐
                   │  Render Call  │
                   └──────┬───────┘
                          │ success / error
                          ▼
                 ┌────────────────┐
                 │ ErrorClassifier│ ← classify stderr / exception
                 └──────┬─────────┘
                        │ RenderDiagnosis
                        ▼
              ┌──────────────────────┐
              │ CorrectionStrategy   │ ← pick automated fix
              └──────────┬───────────┘
                         │ patched env / params
                         ▼
                  ┌──────────────┐
                  │   Retry      │  (up to max_retries)
                  └──────────────┘

Integration points
------------------
- ``orchestrator/runner.py``  — wrap ``run_project_task`` with ``self_correcting_run``
- ``projects/*/renderer/animation.py`` — wrap subprocess call
- ``shared/core/task_manager.py`` — update task status with correction metadata
"""

from __future__ import annotations

import enum
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, TypeVar

from shared.utils.logger import setup_logger

_log = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------

class ErrorCategory(str, enum.Enum):
    """Coarse error buckets that map to correction strategies."""

    MISSING_DEPENDENCY = "missing_dependency"
    FONT_NOT_FOUND = "font_not_found"
    FFMPEG_ERROR = "ffmpeg_error"
    OUT_OF_MEMORY = "out_of_memory"
    INVALID_PARAMETER = "invalid_parameter"
    FILE_NOT_FOUND = "file_not_found"
    TIMEOUT = "timeout"
    MANIM_SCENE_ERROR = "manim_scene_error"
    MATPLOTLIB_ERROR = "matplotlib_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RenderDiagnosis:
    """Structured result of analysing a render failure."""

    category: ErrorCategory
    message: str
    suggested_fix: str
    raw_stderr: str = ""
    auto_correctable: bool = False
    env_patches: dict[str, str] = field(default_factory=dict)
    param_patches: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Classifier — pattern-match stderr / exception into diagnosis
# ---------------------------------------------------------------------------

# (compiled_pattern, category, suggested_fix_template, auto_correctable)
_PATTERNS: list[tuple[re.Pattern[str], ErrorCategory, str, bool]] = [
    # Font fallback
    (
        re.compile(r"(findfont|FontNotFoundError|cannot find font|font.*not found)", re.I),
        ErrorCategory.FONT_NOT_FOUND,
        "Falling back to default safe font (Source Han Sans / Noto Sans SC).",
        True,
    ),
    # FFmpeg binary missing
    (
        re.compile(r"(ffmpeg.*not found|FileNotFoundError.*ffmpeg|'ffmpeg' is not recognized)", re.I),
        ErrorCategory.FFMPEG_ERROR,
        "ffmpeg binary not on PATH. Install ffmpeg>=6.0 or set FFMPEG_BINARY env.",
        False,
    ),
    # FFmpeg encoding error
    (
        re.compile(r"(Error while.*encoding|Avi header|ffmpeg.*error|pipe:.*broken)", re.I),
        ErrorCategory.FFMPEG_ERROR,
        "FFmpeg encoding error — lowering bitrate / switching to yuv420p.",
        True,
    ),
    # Missing Python package
    (
        re.compile(r"(ModuleNotFoundError|ImportError|No module named)", re.I),
        ErrorCategory.MISSING_DEPENDENCY,
        "A required Python package is missing. Check requirements.txt.",
        False,
    ),
    # Manim-specific
    (
        re.compile(r"(manim.*error|Scene.*not found|ManimError|cairo.*error)", re.I),
        ErrorCategory.MANIM_SCENE_ERROR,
        "Manim scene error — check scene class name and construct() logic.",
        False,
    ),
    # Matplotlib
    (
        re.compile(r"(matplotlib.*error|fig.*size|UserWarning.*tight_layout)", re.I),
        ErrorCategory.MATPLOTLIB_ERROR,
        "Matplotlib rendering issue — adjusting figure size / DPI.",
        True,
    ),
    # Out of memory
    (
        re.compile(r"(MemoryError|out of memory|OOM|killed.*signal 9)", re.I),
        ErrorCategory.OUT_OF_MEMORY,
        "Out of memory — reducing resolution or frame batch size.",
        True,
    ),
    # File not found (data files, assets)
    (
        re.compile(r"(FileNotFoundError|No such file|file.*not exist)", re.I),
        ErrorCategory.FILE_NOT_FOUND,
        "Required file not found. Check asset paths and data directory.",
        False,
    ),
    # Parameter / value error
    (
        re.compile(r"(ValueError|InvalidParameterError|out of range|invalid.*param)", re.I),
        ErrorCategory.INVALID_PARAMETER,
        "Invalid parameter value — check CONFIG defaults.",
        False,
    ),
    # Timeout
    (
        re.compile(r"(TimeoutExpired|timed out|timeout)", re.I),
        ErrorCategory.TIMEOUT,
        "Render timed out — lowering quality or reducing frame count.",
        True,
    ),
]


def classify_error(
    stderr: str,
    exception: BaseException | None = None,
    returncode: int | None = None,
) -> RenderDiagnosis:
    """
    Classify a render failure into a ``RenderDiagnosis``.

    Scan *stderr* (and optional exception message) against known patterns.
    """
    text = stderr
    if exception:
        text = f"{text}\n{type(exception).__name__}: {exception}"

    for pattern, category, fix_hint, auto in _PATTERNS:
        if pattern.search(text):
            diagnosis = _build_diagnosis(category, fix_hint, auto, text)
            return diagnosis

    return RenderDiagnosis(
        category=ErrorCategory.UNKNOWN,
        message="Unrecognised render error.",
        suggested_fix="Manual investigation required — see raw stderr.",
        raw_stderr=text[:2000],  # cap for logging
        auto_correctable=False,
    )


def _build_diagnosis(
    category: ErrorCategory,
    fix_hint: str,
    auto: bool,
    raw: str,
) -> RenderDiagnosis:
    """Construct a diagnosis with recommended parameter patches."""
    env_patches: dict[str, str] = {}
    param_patches: dict[str, Any] = {}

    if category == ErrorCategory.FONT_NOT_FOUND:
        env_patches["VIDEO_FONT_FAMILY"] = "Noto Sans SC"

    elif category == ErrorCategory.FFMPEG_ERROR and auto:
        env_patches["VIDEO_PIXEL_FORMAT"] = "yuv420p"
        param_patches["bitrate"] = "8M"

    elif category == ErrorCategory.OUT_OF_MEMORY:
        param_patches["quality"] = "preview"
        env_patches["VIDEO_DPI"] = "72"

    elif category == ErrorCategory.TIMEOUT:
        param_patches["quality"] = "preview"
        param_patches["timeout_secs"] = 1200

    elif category == ErrorCategory.MATPLOTLIB_ERROR and auto:
        env_patches["VIDEO_DPI"] = "100"

    return RenderDiagnosis(
        category=category,
        message=f"[{category.value}] {fix_hint}",
        suggested_fix=fix_hint,
        raw_stderr=raw[:2000],
        auto_correctable=auto,
        env_patches=env_patches,
        param_patches=param_patches,
    )


# ---------------------------------------------------------------------------
# Correction record — persisted for auditability
# ---------------------------------------------------------------------------

@dataclass
class CorrectionRecord:
    """One correction attempt (immutable audit entry)."""

    attempt: int
    diagnosis: RenderDiagnosis
    applied_patches: dict[str, Any]
    succeeded: bool
    elapsed_secs: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "category": self.diagnosis.category.value,
            "message": self.diagnosis.message,
            "auto_correctable": self.diagnosis.auto_correctable,
            "applied_patches": self.applied_patches,
            "succeeded": self.succeeded,
            "elapsed_secs": round(self.elapsed_secs, 2),
        }


@dataclass
class CorrectionReport:
    """Full correction session: original error + all retry attempts."""

    records: list[CorrectionRecord] = field(default_factory=list)
    final_success: bool = False

    @property
    def total_attempts(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_attempts": self.total_attempts,
            "final_success": self.final_success,
            "records": [r.to_dict() for r in self.records],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Self-correcting runner — wraps any callable that may fail
# ---------------------------------------------------------------------------

class SelfCorrectingRunner:
    """
    Wraps a render callable with automatic error classification and retry.

    Usage::

        runner = SelfCorrectingRunner(max_retries=3)
        result = runner.run(
            fn=my_render_function,
            kwargs={"quality": "final", "platform": "bilibili"},
            error_extractor=lambda exc: str(exc),
        )
    """

    def __init__(
        self,
        max_retries: int = 2,
        backoff_base: float = 2.0,
        log_dir: Path | None = None,
    ):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.log_dir = log_dir

    def run(
        self,
        fn: Callable[..., T],
        kwargs: dict[str, Any] | None = None,
        *,
        error_extractor: Callable[[BaseException], str] | None = None,
        on_retry: Callable[[int, RenderDiagnosis], None] | None = None,
    ) -> tuple[T, CorrectionReport]:
        """
        Execute *fn* with automatic retry on classified errors.

        Returns ``(result, report)`` — *report* contains the correction audit trail.
        Raises the original exception if all retries are exhausted.
        """
        kwargs = dict(kwargs or {})
        report = CorrectionReport()
        extract = error_extractor or (lambda e: str(e))
        last_exc: BaseException | None = None

        for attempt in range(self.max_retries + 1):
            t0 = time.monotonic()
            try:
                result = fn(**kwargs)
                # First attempt success or retry success
                if attempt > 0:
                    report.records[-1].succeeded = True
                    report.records[-1].elapsed_secs = time.monotonic() - t0
                report.final_success = True
                self._persist_report(report)
                return result, report

            except BaseException as exc:
                elapsed = time.monotonic() - t0
                last_exc = exc
                stderr_text = extract(exc)
                diagnosis = classify_error(stderr_text, exc)

                record = CorrectionRecord(
                    attempt=attempt + 1,
                    diagnosis=diagnosis,
                    applied_patches={},
                    succeeded=False,
                    elapsed_secs=elapsed,
                )

                if attempt < self.max_retries and diagnosis.auto_correctable:
                    patches = {**diagnosis.env_patches, **diagnosis.param_patches}
                    record.applied_patches = patches

                    # Apply param patches to kwargs for next attempt
                    kwargs.update(diagnosis.param_patches)
                    # Apply env patches
                    import os
                    for k, v in diagnosis.env_patches.items():
                        os.environ[k] = v

                    _log.warning(
                        "Attempt %d/%d failed [%s]. Auto-correcting with patches: %s",
                        attempt + 1,
                        self.max_retries + 1,
                        diagnosis.category.value,
                        patches,
                    )

                    if on_retry:
                        on_retry(attempt + 1, diagnosis)

                    report.records.append(record)

                    # Backoff before retry
                    delay = self.backoff_base ** attempt
                    time.sleep(delay)
                    continue

                else:
                    report.records.append(record)
                    if not diagnosis.auto_correctable:
                        _log.error(
                            "Attempt %d failed [%s] — not auto-correctable. %s",
                            attempt + 1,
                            diagnosis.category.value,
                            diagnosis.suggested_fix,
                        )
                    else:
                        _log.error(
                            "All %d retries exhausted for [%s].",
                            self.max_retries + 1,
                            diagnosis.category.value,
                        )
                    break

        self._persist_report(report)

        assert last_exc is not None
        raise last_exc

    def _persist_report(self, report: CorrectionReport) -> None:
        if self.log_dir and report.total_attempts > 0:
            from shared.utils.time import utc_now
            ts = utc_now().strftime("%Y%m%d_%H%M%S")
            path = self.log_dir / f"correction_{ts}.json"
            try:
                report.save(path)
            except Exception:
                _log.debug("Failed to persist correction report", exc_info=True)


# ---------------------------------------------------------------------------
# Subprocess-oriented helper — for wrapping subprocess.run render calls
# ---------------------------------------------------------------------------

def self_correcting_subprocess(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    timeout: int = 600,
    max_retries: int = 2,
    backoff_base: float = 2.0,
) -> tuple[Any, CorrectionReport]:
    """
    Run a subprocess (e.g. ``python impl.py`` or ``manim ...``) with
    automatic error classification and retry.

    Returns ``(subprocess.CompletedProcess, CorrectionReport)``.
    Raises ``RuntimeError`` if all retries fail.
    """
    import subprocess as sp

    current_env = dict(env or {})
    report = CorrectionReport()

    for attempt in range(max_retries + 1):
        t0 = time.monotonic()
        run_env = {**current_env}

        try:
            proc = sp.run(
                cmd,
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
                text=True,
                check=False,
                cwd=str(cwd) if cwd else None,
                env=run_env,
                timeout=timeout,
            )
        except sp.TimeoutExpired:
            proc = None
            stderr_text = f"TimeoutExpired after {timeout}s"
        else:
            stderr_text = proc.stdout or ""

        elapsed = time.monotonic() - t0

        if proc is not None and proc.returncode == 0:
            if attempt > 0 and report.records:
                report.records[-1].succeeded = True
                report.records[-1].elapsed_secs = elapsed
            report.final_success = True
            return proc, report

        diagnosis = classify_error(stderr_text)

        record = CorrectionRecord(
            attempt=attempt + 1,
            diagnosis=diagnosis,
            applied_patches={},
            succeeded=False,
            elapsed_secs=elapsed,
        )

        if attempt < max_retries and diagnosis.auto_correctable:
            record.applied_patches = {**diagnosis.env_patches, **diagnosis.param_patches}
            current_env.update(diagnosis.env_patches)
            report.records.append(record)

            _log.warning(
                "Subprocess attempt %d/%d failed [%s]. Retrying with patches: %s",
                attempt + 1,
                max_retries + 1,
                diagnosis.category.value,
                record.applied_patches,
            )

            delay = backoff_base ** attempt
            time.sleep(delay)
            continue
        else:
            report.records.append(record)
            break

    last_stderr = report.records[-1].diagnosis.raw_stderr if report.records else stderr_text
    raise RuntimeError(
        f"Render subprocess failed after {report.total_attempts} attempt(s).\n"
        f"Last error [{report.records[-1].diagnosis.category.value}]: "
        f"{report.records[-1].diagnosis.suggested_fix}\n"
        f"stderr:\n{last_stderr[:1000]}"
    )

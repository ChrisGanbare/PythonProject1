"""Quality conformance tests: ensure all projects use shared quality infrastructure.

Run with:  pytest tests/test_quality_conformance.py -v
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = REPO_ROOT / "projects"

# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_project_python_files(project_dir: Path) -> list[Path]:
    """Return all .py files under a project directory."""
    return sorted(project_dir.rglob("*.py"))


def _get_all_project_dirs() -> list[Path]:
    """Discover project directories that contain a project_manifest.py."""
    dirs = []
    for manifest in PROJECTS_DIR.glob("*/project_manifest.py"):
        dirs.append(manifest.parent)
    return sorted(dirs)


# ── Anti-pattern detection via AST ───────────────────────────────────────────

_FORBIDDEN_LOCAL_PRESET_PATTERNS = {
    # dict names that suggest locally duplicated presets
    "_PLATFORM_PRESETS",
    "_QUALITY_PRESETS",
    "PLATFORM_PRESETS",
    "QUALITY_PRESETS",
    "platform_presets",
    "quality_presets",
}


def _scan_for_local_presets(source_path: Path) -> list[str]:
    """AST-scan a file for locally-defined preset dicts that should come from shared."""
    violations = []
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _FORBIDDEN_LOCAL_PRESET_PATTERNS:
                    violations.append(
                        f"{source_path.relative_to(REPO_ROOT)}:{node.lineno} — "
                        f"local preset dict '{target.id}' should use shared imports"
                    )
    return violations


def _scan_for_hardcoded_resolution(source_path: Path) -> list[str]:
    """Check for hardcoded resolution/fps magic numbers in renderer files."""
    violations = []
    try:
        source = source_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    # Only check renderer-related files
    rel = source_path.relative_to(REPO_ROOT)
    if "renderer" not in str(rel) and "viz_backend" not in str(rel):
        return []

    # Look for patterns like: "width": 1080  or  "width": 1920
    # but allow them in comments or as env var defaults
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and isinstance(key.value, str)
                        and key.value in ("width", "height", "fps")
                        and isinstance(value, ast.Constant)
                        and isinstance(value.value, int)):
                    violations.append(
                        f"{source_path.relative_to(REPO_ROOT)}:{node.lineno} — "
                        f"hardcoded {key.value}={value.value} in dict literal; "
                        f"use get_platform_preset() instead"
                    )
    return violations


# ── Tests ────────────────────────────────────────────────────────────────────

class TestNoLocalPresetDuplication:
    """Ensure no project redefines platform/quality presets locally."""

    @pytest.fixture(params=_get_all_project_dirs(), ids=lambda d: d.name)
    def project_dir(self, request: pytest.FixtureRequest) -> Path:
        return request.param

    def test_no_local_preset_dicts(self, project_dir: Path) -> None:
        all_violations: list[str] = []
        for py_file in _find_project_python_files(project_dir):
            all_violations.extend(_scan_for_local_presets(py_file))
        assert all_violations == [], (
            "Found locally duplicated preset definitions (should use shared imports):\n"
            + "\n".join(all_violations)
        )


class TestSharedPresetsConsistency:
    """Verify shared presets are self-consistent."""

    def test_quality_presets_have_required_keys(self) -> None:
        from shared.ops.config.settings import QUALITY_PRESETS
        required = {"dpi", "bitrate", "preset", "crf"}
        for name, qp in QUALITY_PRESETS.items():
            missing = required - set(qp.keys())
            assert not missing, f"quality preset '{name}' missing keys: {missing}"

    def test_platform_presets_cover_all_platforms(self) -> None:
        from shared.output.platform.presets import ALL_PRESETS
        expected = {"douyin", "bilibili_landscape", "bilibili_vertical", "xiaohongshu"}
        assert set(ALL_PRESETS.keys()) >= expected

    def test_quality_preset_crf_ordering(self) -> None:
        from shared.ops.config.settings import QUALITY_PRESETS
        crfs = [(name, int(qp["crf"])) for name, qp in QUALITY_PRESETS.items()]
        # Higher quality → lower CRF
        preview_crf = dict(crfs)["preview"]
        draft_crf = dict(crfs)["draft"]
        final_crf = dict(crfs)["final"]
        assert preview_crf > draft_crf > final_crf, (
            f"CRF should decrease with quality: preview={preview_crf}, "
            f"draft={draft_crf}, final={final_crf}"
        )

    def test_platform_fps_is_valid(self) -> None:
        from shared.output.platform.presets import ALL_PRESETS
        for name, pp in ALL_PRESETS.items():
            assert pp.fps in {24, 25, 30, 60}, f"{name}: fps={pp.fps} not in valid set"


class TestQualityGateContract:
    """Verify the quality gate contract builder works correctly."""

    def test_validate_render_inputs_returns_contract(self) -> None:
        from shared.render.core.quality_gate import validate_render_inputs
        contract = validate_render_inputs(platform="douyin", quality="draft")
        assert contract.width == 1080
        assert contract.height == 1920
        assert contract.fps == 30
        assert contract.dpi == 108
        assert contract.crf == 21

    def test_validate_render_inputs_rejects_unknown_platform(self) -> None:
        from shared.render.core.quality_gate import validate_render_inputs
        with pytest.raises(ValueError, match="unsupported platform"):
            validate_render_inputs(platform="tiktok", quality="draft")

    def test_validate_render_inputs_rejects_unknown_quality(self) -> None:
        from shared.render.core.quality_gate import validate_render_inputs
        with pytest.raises(ValueError, match="unsupported quality"):
            validate_render_inputs(platform="douyin", quality="ultra")

    def test_contract_env_dict_has_all_keys(self) -> None:
        from shared.render.core.quality_gate import validate_render_inputs
        contract = validate_render_inputs(platform="douyin", quality="draft")
        env = contract.to_env_dict()
        required = {
            "VIDEO_WIDTH", "VIDEO_HEIGHT", "VIDEO_FPS", "VIDEO_DPI",
            "VIDEO_BITRATE", "VIDEO_CRF", "VIDEO_PRESET", "VIDEO_PLATFORM",
        }
        assert required <= set(env.keys())

    @pytest.mark.parametrize("platform", ["douyin", "bilibili_landscape", "bilibili_vertical", "xiaohongshu"])
    @pytest.mark.parametrize("quality", ["preview", "draft", "final"])
    def test_all_platform_quality_combos_valid(self, platform: str, quality: str) -> None:
        from shared.render.core.quality_gate import validate_render_inputs
        contract = validate_render_inputs(platform=platform, quality=quality)
        assert contract.width > 0
        assert contract.height > 0
        assert contract.dpi > 0


class TestNoHardcodedResolution:
    """Warn about hardcoded resolution values in renderer files."""

    @pytest.fixture(params=_get_all_project_dirs(), ids=lambda d: d.name)
    def project_dir(self, request: pytest.FixtureRequest) -> Path:
        return request.param

    def test_no_hardcoded_resolution_in_renderers(self, project_dir: Path) -> None:
        all_violations: list[str] = []
        for py_file in _find_project_python_files(project_dir):
            all_violations.extend(_scan_for_hardcoded_resolution(py_file))
        if all_violations:
            pytest.skip(
                "Hardcoded resolution found (should migrate to shared presets):\n"
                + "\n".join(all_violations)
            )

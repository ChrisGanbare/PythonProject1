"""Shared typography helper tests."""

from __future__ import annotations

from types import SimpleNamespace

from shared.content.typography import (
    apply_matplotlib_typography,
    build_font_candidates,
    normalize_font_weight,
    resolve_available_font,
)


def test_build_font_candidates_deduplicates_and_keeps_order() -> None:
    candidates = build_font_candidates(
        "Source Han Sans SC",
        ["Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei"],
    )
    assert candidates == ["Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei"]


def test_normalize_font_weight_maps_common_aliases() -> None:
    assert normalize_font_weight("regular") == "normal"
    assert normalize_font_weight("semi-bold") == "semibold"
    assert normalize_font_weight("BOLD") == "bold"
    assert normalize_font_weight(None, fallback="medium") == "medium"


def test_resolve_available_font_uses_first_existing_candidate(monkeypatch) -> None:
    fake_fonts = [SimpleNamespace(name="Microsoft YaHei"), SimpleNamespace(name="DejaVu Sans")]
    monkeypatch.setattr("shared.content.typography.fm.fontManager.ttflist", fake_fonts)
    assert resolve_available_font(["Source Han Sans SC", "Microsoft YaHei", "DejaVu Sans"]) == "Microsoft YaHei"


def test_apply_matplotlib_typography_prefers_available_font(monkeypatch) -> None:
    fake_fonts = [SimpleNamespace(name="Microsoft YaHei"), SimpleNamespace(name="DejaVu Sans")]
    monkeypatch.setattr("shared.content.typography.fm.fontManager.ttflist", fake_fonts)
    resolved = apply_matplotlib_typography(
        {
            "font_family": "Source Han Sans SC",
            "font_fallbacks": ["Microsoft YaHei", "DejaVu Sans"],
        }
    )
    assert resolved == "Microsoft YaHei"


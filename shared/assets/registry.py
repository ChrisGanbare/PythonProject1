"""Asset registry and manager."""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.config.settings import settings
from shared.content.screenplay import Mood, VisualStyle


class AssetType(str, Enum):
    FONT = "font"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEMPLATE = "template"


class Asset(BaseModel):
    id: str
    type: AssetType
    path: Path
    description: str
    tags: List[str] = []
    mood: Optional[Mood] = None
    style: Optional[VisualStyle] = None


def _slug_id(prefix: str, name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    return f"{prefix}_{s}" if s else prefix


class AssetManager:
    """Resolves abstract asset references: built-ins + `assets/library/registry.json` + directory scan."""

    def __init__(self, assets_dir: Optional[Path] = None):
        self.assets_dir = (assets_dir or settings.project_root / "assets").resolve()
        self._assets: Dict[str, Asset] = {}
        self._load_registry()

    def _register(self, asset: Asset) -> None:
        self._assets[asset.id] = asset

    def _load_registry(self) -> None:
        self._register(
            Asset(
                id="font_title_minimal",
                type=AssetType.FONT,
                path=self.assets_dir / "fonts" / "SourceHanSansSC-Bold.otf",
                description="Bold sans-serif font for titles",
                style=VisualStyle.MINIMALIST,
            )
        )

        self._register(
            Asset(
                id="font_body_minimal",
                type=AssetType.FONT,
                path=self.assets_dir / "fonts" / "SourceHanSansSC-Regular.otf",
                description="Clean sans-serif font for body text",
                style=VisualStyle.MINIMALIST,
            )
        )

        self._register(
            Asset(
                id="music_upbeat_01",
                type=AssetType.AUDIO,
                path=self.assets_dir / "sounds" / "upbeat_corporate.mp3",
                description="Upbeat corporate background music",
                mood=Mood.UPBEAT,
            )
        )

        self._register(
            Asset(
                id="template_loan_comparison",
                type=AssetType.TEMPLATE,
                path=self.assets_dir / "templates" / "loan_comparison.json",
                description="Standard loan comparison chart template",
                style=VisualStyle.DATA_DRIVEN,
            )
        )

        self._load_json_manifest()
        self._scan_audio_and_fonts()

    def _load_json_manifest(self) -> None:
        manifest_path = self.assets_dir / "library" / "registry.json"
        if not manifest_path.exists():
            return
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            return
        entries = raw if isinstance(raw, list) else raw.get("assets", [])
        if not isinstance(entries, list):
            return
        for item in entries:
            if not isinstance(item, dict):
                continue
            aid = str(item.get("id", "")).strip()
            rel = str(item.get("path", item.get("relative_path", ""))).strip()
            if not aid or not rel:
                continue
            at = str(item.get("type", "audio")).lower()
            try:
                asset_type = AssetType(at)
            except ValueError:
                continue
            path = (self.assets_dir / rel).resolve()
            mood_raw, style_raw = item.get("mood"), item.get("style")
            mood_enum = None
            style_enum = None
            if isinstance(mood_raw, str):
                try:
                    mood_enum = Mood(mood_raw)
                except ValueError:
                    mood_enum = None
            if isinstance(style_raw, str):
                try:
                    style_enum = VisualStyle(style_raw)
                except ValueError:
                    style_enum = None
            self._register(
                Asset(
                    id=aid,
                    type=asset_type,
                    path=path,
                    description=str(item.get("description", aid)),
                    tags=list(item.get("tags", [])) if isinstance(item.get("tags"), list) else [],
                    mood=mood_enum,
                    style=style_enum,
                )
            )

    def _scan_audio_and_fonts(self) -> None:
        sounds = self.assets_dir / "sounds"
        if sounds.is_dir():
            for p in sounds.glob("*"):
                if p.suffix.lower() not in {".mp3", ".wav", ".aac", ".m4a", ".ogg"}:
                    continue
                aid = _slug_id("audio", p.stem)
                if aid in self._assets:
                    continue
                self._register(
                    Asset(
                        id=aid,
                        type=AssetType.AUDIO,
                        path=p.resolve(),
                        description=f"Scanned audio: {p.name}",
                        tags=["scanned"],
                    )
                )

        fonts = self.assets_dir / "fonts"
        if fonts.is_dir():
            for p in fonts.glob("*"):
                if p.suffix.lower() not in {".otf", ".ttf", ".ttc"}:
                    continue
                aid = _slug_id("font", p.stem)
                if aid in self._assets:
                    continue
                self._register(
                    Asset(
                        id=aid,
                        type=AssetType.FONT,
                        path=p.resolve(),
                        description=f"Scanned font: {p.name}",
                        tags=["scanned"],
                    )
                )

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get(asset_id)

    def resolve_path(self, asset_id: str) -> Optional[Path]:
        asset = self.get_asset(asset_id)
        if asset:
            return asset.path
        return None

    def list_assets(self) -> List[Asset]:
        return sorted(self._assets.values(), key=lambda a: a.id)

    def find_assets(
        self,
        type: AssetType,
        mood: Optional[Mood] = None,
        style: Optional[VisualStyle] = None,
    ) -> List[Asset]:
        matches = []
        for asset in self._assets.values():
            if asset.type == type:
                if mood and asset.mood and asset.mood != mood:
                    continue
                if style and asset.style and asset.style != style:
                    continue
                matches.append(asset)
        return matches

    def validate_ids(self, asset_ids: list[str]) -> tuple[bool, list[str]]:
        """Return (all_exist, missing_ids)."""
        missing = [i for i in asset_ids if i not in self._assets]
        return (not missing, missing)


asset_manager = AssetManager()


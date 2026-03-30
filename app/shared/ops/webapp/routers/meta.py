"""统一 HTTP 架构说明（机器可读），与 OpenAPI 并列作为集成契约入口。"""

from __future__ import annotations

from fastapi import APIRouter

from shared.ops.webapp.domain_mounts import DOMAIN_APP_SPECS

router = APIRouter(tags=["architecture"])


@router.get("/api/meta/architecture")
def http_architecture() -> dict:
    """权威前缀与领域挂载清单；探活请用 ``GET /api/studio/v1/health``。"""
    return {
        "schema_version": 1,
        "canonical_prefixes": {
            "studio_control_plane": "/api/studio/v1",
            "quick_video_v2": "/api/video/v2",
            "static_assets": "/static",
            "legacy_redirects": "deprecated root paths under /api/agent/* and /api/jobs* redirect 307 to /api/studio/v1",
        },
        "domain_mounts": [
            {
                "name": name,
                "mount_path": f"/api/domain/{name}",
                "module": mod_path,
                "note": "sub-app mount; separate OpenAPI at mount_path/docs when mounted",
            }
            for name, mod_path in DOMAIN_APP_SPECS
        ],
        "readiness_probe": "/api/studio/v1/health",
    }

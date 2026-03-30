"""控制台 HTTP 子路由（按模块拆分）。"""

from shared.ops.webapp.routers.legacy_redirects import router as legacy_redirects_router
from shared.ops.webapp.routers.meta import router as meta_router
from shared.ops.webapp.routers.pages import STATIC_DIR, router as pages_router
from shared.ops.webapp.routers.projects import router as projects_router
from shared.ops.webapp.routers.screenplay_proxy import router as screenplay_proxy_router
from shared.ops.webapp.routers.settings import router as settings_router

__all__ = [
    "STATIC_DIR",
    "legacy_redirects_router",
    "meta_router",
    "pages_router",
    "projects_router",
    "screenplay_proxy_router",
    "settings_router",
]

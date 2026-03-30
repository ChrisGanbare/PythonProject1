"""FastAPI lifespan：项目发现、Studio DB、可选自动打开浏览器。"""

from __future__ import annotations

import asyncio
import logging
import os
import webbrowser
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.ops.studio.db.init import init_db
from shared.ops.webapp.env_settings import env_truthy
from shared.ops.webapp.state import registry

logger = logging.getLogger("dashboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Discovering projects...")
    registry.discover()
    init_db()
    logger.info("Studio control plane database ready.")
    if env_truthy("DASHBOARD_OPEN_BROWSER"):
        host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
        port = int(os.environ.get("DASHBOARD_PORT", "8090"))
        url = f"http://{host}:{port}/"

        async def _open_browser_after_ready() -> None:
            await asyncio.sleep(1.0)
            try:
                webbrowser.open(url)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not open browser (%s): %s", url, exc)

        asyncio.create_task(_open_browser_after_ready())
    yield

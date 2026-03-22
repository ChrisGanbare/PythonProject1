#!/usr/bin/env bash
# Web 控制台启动脚本（macOS / Linux）。仓库根目录执行：chmod +x run_dashboard.sh && ./run_dashboard.sh
set -euo pipefail
cd "$(dirname "$0")"
echo "Starting Video Project Control Center..."
export DASHBOARD_OPEN_BROWSER=1
exec python dashboard.py

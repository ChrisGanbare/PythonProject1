@echo off
cd /d "%~dp0"
set DASHBOARD_OPEN_BROWSER=1
echo Starting Video Project Control Center...
python dashboard.py
pause

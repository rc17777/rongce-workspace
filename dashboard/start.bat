@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ╔════════════════════════════════════╗
echo ║  融策 Agent 状态监控面板 v1.0     ║
echo ║  启动中...                         ║
echo ╚════════════════════════════════════╝
echo.
python server.py
pause

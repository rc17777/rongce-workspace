@echo off
chcp 65001 >nul
title 智析智能体 v2.0 — 审计数据分析平台
setlocal EnableDelayedExpansion

cd /d "%~dp0"

echo.
echo   ╔══════════════════════════════════════════════════╗
echo   ║     智析智能体 v2.0 — 审计数据分析平台        ║
echo   ║     融策会计师事务所 · 2026                    ║
echo   ╚══════════════════════════════════════════════════╝
echo.

:: ============================================================
:: 检测 Python
:: ============================================================
echo   [INFO] 检测 Python 环境...
where python >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
python --version

:: ============================================================
:: 检查端口
:: ============================================================
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5002.*LISTENING" 2^>nul') do (
    echo   [提示] 端口 5002 已被占用 (PID: %%a)，正在关闭...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: ============================================================
:: 安装依赖（首次运行）
:: ============================================================
if not exist ".deps_ok" (
    echo   [INFO] 首次运行，安装核心依赖...
    python -m pip install flask flask-cors pandas numpy openpyxl python-docx PyPDF2 Pillow networkx jieba requests --quiet
    if errorlevel 1 (
        echo   [WARN] 部分依赖安装失败，可手动安装
    ) else (
        echo. > .deps_ok
    )
)

:: ============================================================
:: 启动
:: ============================================================
echo.
echo   [启动] 正在启动智析智能体 v2.0...
echo.
start http://127.0.0.1:5002
python app.py

pause

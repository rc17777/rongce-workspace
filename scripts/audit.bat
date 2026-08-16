@echo off
REM ============================================
REM  招投标审计一键分析 — Windows批处理快捷入口
REM  双击运行或拖拽项目文件夹到此文件
REM ============================================
setlocal enabledelayedexpansion

if "%1"=="" (
    echo 用法: 将项目文件夹拖拽到此批处理文件上
    echo 或: audit.bat C:\path\to\project
    pause
    exit /b
)

set PROJECT_DIR=%1
set OUTPUT_DIR=%PROJECT_DIR%\audit_output
set PYTHON=C:\Users\scrccpa\AppData\Local\Programs\Python\Python314\python.exe
set SCRIPT=D:\openclaw-workspace\scripts\audit_pipeline.py

echo ============================================
echo  招投标审计全流程分析
echo ============================================
echo 项目: %PROJECT_DIR%
echo 输出: %OUTPUT_DIR%
echo.

%PYTHON% "%SCRIPT%" --project "%PROJECT_DIR%" --type procurement --o "%OUTPUT_DIR%"

echo.
echo ============================================
echo 分析完成! 结果在: %OUTPUT_DIR%
echo ============================================
echo.
echo 打开输出文件夹...
explorer "%OUTPUT_DIR%"
pause

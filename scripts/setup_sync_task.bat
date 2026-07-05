@echo off
chcp 65001 >nul
setlocal

:: ============================================================
:: setup_sync_task.bat - Create Windows Scheduled Task for auto sync
:: Run: Right-click -> Run as Administrator
:: ============================================================

echo.
echo ==============================================
echo   OpenClaw Workspace Git Auto Sync Installer
echo ==============================================
echo.

:: --- Config ---
set TASK_NAME=OpenClaw_Workspace_Sync
set SCRIPT_DIR=%~dp0
set SYNC_BAT=%SCRIPT_DIR%sync_git.bat
set INTERVAL_MIN=30

:: --- Check admin privileges ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Please run as Administrator!
    echo        Right-click -> Run as Administrator
    pause
    exit /b 1
)

:: --- Check sync_git.bat exists ---
if not exist "%SYNC_BAT%" (
    echo [FAIL] Cannot find sync_git.bat: %SYNC_BAT%
    echo        Make sure both scripts are in the same folder.
    pause
    exit /b 1
)

echo [INFO] Task name  : %TASK_NAME%
echo [INFO] Sync script: %SYNC_BAT%
echo [INFO] Interval   : Every %INTERVAL_MIN% minutes
echo.

:: --- Remove old task if exists ---
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] Removing old task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul
    echo        Removed.
)

:: --- Create scheduled task ---
echo [INFO] Creating scheduled task...

for /f "tokens=1-2 delims=:" %%a in ('time /t') do (
    set HOUR=%%a
    set MIN=%%b
)
set HOUR=%HOUR: =0%

schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%SYNC_BAT%\"" ^
    /sc minute ^
    /mo %INTERVAL_MIN% ^
    /st %HOUR%:%MIN% ^
    /ru SYSTEM ^
    /rl highest ^
    /f

if %errorlevel% neq 0 (
    echo.
    echo [INFO] SYSTEM account not available, trying current user...
    
    schtasks /create ^
        /tn "%TASK_NAME%" ^
        /tr "\"%SYNC_BAT%\"" ^
        /sc minute ^
        /mo %INTERVAL_MIN% ^
        /f
    
    if %errorlevel% neq 0 (
        echo [FAIL] Cannot create task. Please create it manually.
        pause
        exit /b 1
    )
)

echo.
echo ==============================================
echo   [OK] Scheduled task created!
echo ==============================================
echo   Task   : %TASK_NAME%
echo   Run    : Every %INTERVAL_MIN% min
echo   Log    : scripts\sync_log.txt
echo ==============================================
echo   Manual test run:
echo   schtasks /run /tn "%TASK_NAME%"
echo ==============================================
echo.
echo Press any key to exit...
pause >nul
exit /b 0

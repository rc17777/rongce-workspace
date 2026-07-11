@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: sync_git.bat - Git auto sync script
:: Run manually or via Scheduled Task
:: ============================================================

:: --- Config ---
set WORKSPACE=D:\openclaw-workspace
set BRANCH=master
set LOGFILE=%WORKSPACE%\scripts\sync_log.txt

:: --- Navigate to workspace ---
cd /d "%WORKSPACE%"
if errorlevel 1 (
    echo [%date% %time%] ERROR: Cannot enter workspace %WORKSPACE% >> "%LOGFILE%"
    exit /b 1
)

:: --- Pull remote changes ---
echo [%date% %time%] Pulling remote updates... >> "%LOGFILE%"
git pull --rebase origin %BRANCH% 2>> "%LOGFILE%"
if errorlevel 1 (
    echo [%date% %time%] WARNING: Pull conflict or failure, skip this sync >> "%LOGFILE%"
    exit /b 1
)

:: --- Check for local changes ---
git diff --quiet
set HAS_UNSTAGED=%errorlevel%

git diff --cached --quiet
set HAS_STAGED=%errorlevel%

if %HAS_UNSTAGED%==0 if %HAS_STAGED%==0 (
    echo [%date% %time%] OK: No changes to sync >> "%LOGFILE%"
    exit /b 0
)

:: --- Stage and commit ---
git add -A
if errorlevel 1 (
    echo [%date% %time%] ERROR: git add failed >> "%LOGFILE%"
    exit /b 1
)

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
git commit -m "auto sync: %TIMESTAMP%" 2>> "%LOGFILE%"
if errorlevel 1 (
    echo [%date% %time%] SKIP: Nothing to commit >> "%LOGFILE%"
    exit /b 0
)

:: --- Push to remote ---
git push origin %BRANCH% 2>> "%LOGFILE%"
if errorlevel 1 (
    echo [%date% %time%] ERROR: git push failed, check network or credentials >> "%LOGFILE%"
    exit /b 1
)

echo [%date% %time%] DONE: Sync completed >> "%LOGFILE%"
exit /b 0

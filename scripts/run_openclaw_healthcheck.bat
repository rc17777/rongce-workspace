@echo off
chcp 65001 >nul
cd /d C:\Users\scrccpa\.openclaw\workspace
if not exist logs mkdir logs
echo [%date% %time%] OpenClaw model healthcheck start >> logs\openclaw_healthcheck_task.log
python scripts\openclaw_healthcheck.py --timeout 20 --quiet-ok >> logs\openclaw_healthcheck_task.log 2>&1
set EXITCODE=%ERRORLEVEL%
echo [%date% %time%] OpenClaw model healthcheck exit=%EXITCODE% >> logs\openclaw_healthcheck_task.log
exit /b %EXITCODE%

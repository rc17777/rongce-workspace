# setup-sync.ps1 — 一键配置 OpenClaw 工作区多机同步
# 放到 workspace 根目录，右键"使用 PowerShell 运行" 或：
#   powershell -ExecutionPolicy Bypass -File setup-sync.ps1

$ErrorActionPreference = "Stop"

# 自动检测 workspace 路径（本脚本所在目录）
$workspace = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Workspace: $workspace" -ForegroundColor Cyan

# 检测 git
$git = @(
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files (x86)\Git\bin\git.exe",
    "$env:LOCALAPPDATA\Programs\Git\bin\git.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $git) {
    Write-Host "❌ 未找到 Git，请先安装 Git for Windows" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
Write-Host "Git: $git" -ForegroundColor Green

# 确保 sync-workspace.ps1 存在
$syncScript = Join-Path $workspace "scripts\sync-workspace.ps1"
if (-not (Test-Path $syncScript)) {
    Write-Host "❌ 未找到 $syncScript，请先 git pull" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 确保 temp 目录存在
$tempDir = Join-Path $workspace "temp"
New-Item -Path $tempDir -ItemType Directory -Force -ErrorAction SilentlyContinue | Out-Null

# 删除旧任务（如存在）
schtasks /delete /tn "OpenClaw工作区同步" /f 2>$null | Out-Null

# 创建新任务
$taskCmd = "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File '$syncScript' > '$tempDir\sync-log.txt' 2>&1"
$taskName = "OpenClaw工作区同步"

schtasks /create /tn $taskName /tr $taskCmd /sc minute /mo 15 /ru "$env:USERNAME" /f

Write-Host "✅ 同步任务已配置！每 15 分钟自动 git pull+push" -ForegroundColor Green
Write-Host "   任务名: $taskName" -ForegroundColor Green
Write-Host "   日志: $tempDir\sync-log.txt" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️ 确保本机能访问 GitHub（如需代理请先开代理）" -ForegroundColor Yellow

Read-Host "按回车退出"

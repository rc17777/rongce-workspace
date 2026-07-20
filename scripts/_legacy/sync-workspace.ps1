# sync-workspace.ps1 — OpenClaw 工作区多机自动同步
# 用法: powershell -ExecutionPolicy Bypass -File sync-workspace.ps1
# 放每台机器的 workspace 根目录，配成 cron / 计划任务每 15 分钟跑一次

param(
    [switch]$DryRun,        # 只检查不执行
    [switch]$PullOnly,      # 只拉不推
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
$workspace = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$git = "C:\Program Files\Git\bin\git.exe"

# 检查 git 是否存在
if (-not (Test-Path $git)) {
    # 尝试其他常见路径
    $git = Get-Command git -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $git) {
        Write-Host "[SYNC] ❌ Git 未找到，跳过同步" -ForegroundColor Red
        exit 1
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "[SYNC] ====== $timestamp =====" -ForegroundColor Cyan

# 进入 workspace
Push-Location $workspace

try {
    # === Step 1: 检查网络连通性 ===
    try {
        $null = Invoke-WebRequest -Uri "https://github.com" -TimeoutSec 5 -UseBasicParsing
    } catch {
        Write-Host "[SYNC] ⚠️ GitHub 不可达（可能需开代理），跳过" -ForegroundColor Yellow
        exit 0
    }

    # === Step 2: 暂存本地未提交的改动 ===
    $hasStash = $false
    $localChanges = & $git status --porcelain 2>&1
    if ($localChanges -and $LASTEXITCODE -eq 0) {
        Write-Host "[SYNC] 📦 暂存本地改动..."
        & $git stash push -m "auto-sync-stash-$((Get-Date).ToString('yyyyMMddHHmmss'))" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $hasStash = $true }
    }

    # === Step 3: 从远程拉取 ===
    Write-Host "[SYNC] ⬇️ 拉取远程更新..."
    $pullResult = & $git pull origin master --no-rebase 2>&1
    if ($LASTEXITCODE -ne 0) {
        $pullError = $pullResult -join "`n"
        Write-Host "[SYNC] ⚠️ Pull 失败: $pullError" -ForegroundColor Yellow
        if ($hasStash) { & $git stash pop 2>&1 | Out-Null }
        exit 1
    }

    # 检查是否有更新
    if ($pullResult -match "Already up to date") {
        Write-Host "[SYNC] ✅ 已是最新"
    } else {
        Write-Host "[SYNC] ✅ 已同步远程更新"
    }

    if ($PullOnly) {
        if ($hasStash) { & $git stash pop 2>&1 | Out-Null }
        Write-Host "[SYNC] 🏁 PullOnly 模式完成"
        exit 0
    }

    # === Step 4: 恢复本地改动 ===
    if ($hasStash) {
        Write-Host "[SYNC] 📤 恢复本地改动..."
        & $git stash pop 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[SYNC] ⚠️ Stash pop 冲突，保留 stash，请手动处理" -ForegroundColor Yellow
            exit 1
        }
    }

    # === Step 5: 检查是否有需要推送的内容 ===
    $changed = & $git status --porcelain 2>&1 | Where-Object { $_ -match '^[MADRCU\?\ ]' }
    if (-not $changed) {
        Write-Host "[SYNC] ✅ 无本地改动需推送"
        exit 0
    }

    # 只自动提交 skills/ 和 knowledge/ 和核心文件
    $toAdd = @()
    foreach ($line in $changed) {
        $file = $line.Substring(3).Trim()
        # 跳过不该自动提交的
        if ($file -match '^\.secrets/' -or 
            $file -match '^config/' -or 
            $file -match '^output/' -or 
            $file -match '^temp/' -or 
            $file -match '^\.openclaw/' -or
            $file -match '\.dreams/' -or
            $file -match 'deepseek_model_last_check') {
            continue
        }
        $toAdd += $file
    }

    if ($toAdd.Count -eq 0) {
        Write-Host "[SYNC] ✅ 所有改动在忽略列表中，跳过"
        exit 0
    }

    if ($DryRun) {
        Write-Host "[SYNC] 🔍 DryRun — 将提交以下文件:"
        $toAdd | ForEach-Object { Write-Host "  $_" }
        exit 0
    }

    # === Step 6: 提交并推送 ===
    Write-Host "[SYNC] 📝 提交 $($toAdd.Count) 个文件..."
    & $git add @toAdd 2>&1 | Out-Null
    $hostname = $env:COMPUTERNAME
    $commitMsg = "auto-sync: $hostname @ $(Get-Date -Format 'yyyy-MM-dd HH:mm') [$($toAdd.Count) files]"
    & $git commit -m $commitMsg 2>&1 | Out-Null

    if ($LASTEXITODE -eq 0) {
        Write-Host "[SYNC] ⬆️ 推送到远程..."
        $pushResult = & $git push origin master 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SYNC] ✅ 推送成功" -ForegroundColor Green
        } else {
            Write-Host "[SYNC] ❌ 推送失败: $pushResult" -ForegroundColor Red
            exit 1
        }
    }

} catch {
    Write-Host "[SYNC] ❌ 异常: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host "[SYNC] 🏁 完成" -ForegroundColor Green

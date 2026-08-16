# git-auto-sync.ps1 - Rongce workspace auto sync to GitHub
# Triggers: login (Startup folder) + manual
# Log: workspace/sync.log

$ErrorActionPreference = "Continue"
$repoPath = "C:\Users\15528\.openclaw\workspace"
$gitExe = "C:\Program Files\Git\cmd\git.exe"
$logFile = Join-Path $repoPath "sync.log"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

Log "=== sync start ==="

Set-Location $repoPath

# check for changes
$status = & $gitExe status --porcelain 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "ERROR: git status failed - $status"
    exit 1
}

$hasChanges = ($status | Where-Object { $_ -match "^(M|A|\?\?)" }).Count
if ($hasChanges -eq 0) {
    Log "no changes, skip"
    exit 0
}

# add tracked dirs
& $gitExe add knowledge/ references/ skills/ audit-plugin/ agents/ memory/ articles/ scripts/ config/ workflows/ 2>&1 | ForEach-Object { Log $_ }
& $gitExe add -u 2>&1 | ForEach-Object { Log $_ }

# check staged
$diff = & $gitExe diff --cached --stat 2>&1
if ($diff -eq $null -or $diff.Count -eq 0) {
    Log "nothing staged, skip"
    exit 0
}

# commit
$now = Get-Date -Format "yyyyMMdd-HHmmss"
$commitMsg = "auto-sync-$now"
& $gitExe commit -m $commitMsg 2>&1 | ForEach-Object { Log $_ }
if ($LASTEXITCODE -ne 0) {
    Log "WARN: commit may have failed"
}

# push
& $gitExe push origin master 2>&1 | ForEach-Object { Log $_ }
if ($LASTEXITCODE -ne 0) {
    Log "WARN: push failed, trying force"
    & $gitExe push --force origin master 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Log "ERROR: force push also failed"
        exit 1
    }
}

Log "sync done: $commitMsg"

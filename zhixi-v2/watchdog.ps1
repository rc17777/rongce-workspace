# 智析智能体 v2.0 — Watchdog
# 每10分钟由 Windows 计划任务触发，监控端口 5002
# 服务挂掉自动重启

$Port = 5002
$ProjectDir = "D:\openclaw-workspace\zhixi-v2"
$PythonExe  = "C:\Users\scrccpa\AppData\Local\Programs\Python\Python314\python.exe"
$AppFile    = "$ProjectDir\app.py"
$LogDir     = "$ProjectDir\logs"
$LogFile    = "$LogDir\watchdog.log"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

Function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts [zhixi-v2 watchdog] $msg"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

# 1. Check if port is already listening
$conn = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($conn.TcpTestSucceeded) {
    # Service is running normally, silent exit
    exit 0
}

# 2. Port not listening, kill ALL stale zhixi-v2 processes
Write-Log "Port $Port not listening, preparing to restart service"

$allStale = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
    try { $_.CommandLine -match "zhixi-v2\\app\.py" } catch { $false }
}
if ($allStale) {
    foreach ($p in $allStale) {
        Write-Log "Killing stale process PID=$($p.Id)"
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
}

# Confirm port is free
$conn2 = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($conn2.TcpTestSucceeded) {
    Write-Log "Port already occupied by another process, aborting start"
    exit 0
}

# 3. Start the service
Write-Log "Starting ZhiXi Agent v2.0..."
try {
    $proc = Start-Process -FilePath $PythonExe `
        -ArgumentList $AppFile `
        -WorkingDirectory $ProjectDir `
        -WindowStyle Hidden `
        -PassThru

    Start-Sleep -Seconds 8

    # 4. Verify startup
    $verify = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($verify.TcpTestSucceeded) {
        Write-Log "Startup successful (PID=$($proc.Id)) - port $Port now listening"
    } else {
        $exited = if ($proc.HasExited) { "yes, exit code=$($proc.ExitCode)" } else { "no" }
        Write-Log "Startup may have failed (PID=$($proc.Id), hasExited=$exited)"
    }
} catch {
    Write-Log "Startup exception: $_"
}

exit 0

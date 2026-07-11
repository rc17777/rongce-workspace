$ErrorActionPreference = 'Continue'
$log = Join-Path $env:TEMP 'openclaw\gateway-entry-fix-2026-07-05.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
function Log($msg) { "[$(Get-Date -Format o)] $msg" | Tee-Object -FilePath $log -Append }

Log 'begin gateway entry fix'
$npmOpenClaw = 'C:\Users\scrccpa\AppData\Roaming\npm\openclaw.cmd'
$gatewayCmd = 'C:\Users\scrccpa\.openclaw\gateway.cmd'

Log "npm openclaw path: $npmOpenClaw"
if (-not (Test-Path $npmOpenClaw)) {
  Log 'ERROR: npm openclaw.cmd not found'
  exit 10
}

Log 'npm openclaw version:'
& $npmOpenClaw --version 2>&1 | Tee-Object -FilePath $log -Append

Log 'stopping existing OpenClaw scheduled task if present'
schtasks /End /TN "OpenClaw Gateway" 2>&1 | Tee-Object -FilePath $log -Append

Log 'stopping OneClaw desktop and helper processes'
Get-Process -Name 'OneClaw Helper','OneClaw' -ErrorAction SilentlyContinue | ForEach-Object {
  Log "stopping process $($_.ProcessName) pid=$($_.Id) path=$($_.Path)"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 5

Log 'checking port 18789 after stop'
$netstat = netstat -ano | findstr :18789
$netstat | Tee-Object -FilePath $log -Append
if ($netstat -match 'LISTENING\s+(\d+)') {
  $pidToStop = [int]$Matches[1]
  Log "port still held by pid=$pidToStop, stopping it"
  Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 3
}

Log "writing gateway launcher: $gatewayCmd"
$launcher = @"
@echo off
"$npmOpenClaw" gateway run %*
"@
Set-Content -Path $gatewayCmd -Value $launcher -Encoding ASCII
Get-Content $gatewayCmd 2>&1 | Tee-Object -FilePath $log -Append

Log 'reinstalling gateway scheduled task via npm OpenClaw'
& $npmOpenClaw gateway uninstall 2>&1 | Tee-Object -FilePath $log -Append
& $npmOpenClaw gateway install 2>&1 | Tee-Object -FilePath $log -Append

Log 'starting gateway service via npm OpenClaw'
& $npmOpenClaw gateway start 2>&1 | Tee-Object -FilePath $log -Append
Start-Sleep -Seconds 10

Log 'gateway status via npm OpenClaw'
& $npmOpenClaw gateway status 2>&1 | Tee-Object -FilePath $log -Append

Log 'openclaw status via npm OpenClaw'
& $npmOpenClaw status 2>&1 | Tee-Object -FilePath $log -Append

Log 'processes after fix'
wmic process where "name='OneClaw.exe' or name='OneClaw Helper.exe' or name='node.exe'" get ProcessId,ParentProcessId,CommandLine,ExecutablePath 2>&1 | Tee-Object -FilePath $log -Append

Log 'end gateway entry fix'
Get-Content $log -Tail 160

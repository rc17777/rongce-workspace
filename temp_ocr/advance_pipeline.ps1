# OCR Pipeline Advancer v2 - fixed Unicode matching
$ErrorActionPreference = 'Stop'

$workspace = 'C:\Users\scrccpa\.openclaw\workspace'
$tempDir = Join-Path $workspace 'temp_ocr'
$logs = Join-Path $tempDir 'ocr_log.txt'
$stateFile = Join-Path $tempDir 'pipeline_state.json'
$stdoutLog = Join-Path $tempDir 'ocr_stdout.log'
$stderrLog = Join-Path $tempDir 'ocr_stderr.log'

if (-not (Test-Path $stateFile)) {
    @{ stage = 'wait_jicha8'; updated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') } | ConvertTo-Json | Set-Content $stateFile
}

$state = Get-Content $stateFile -Raw | ConvertFrom-Json
$logText = if (Test-Path $logs) { Get-Content $logs -Tail 100 -Encoding UTF8 -ErrorAction SilentlyContinue | Out-String } else { '' }

function Save-State($newStage) {
    @{ stage = $newStage; updated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') } | ConvertTo-Json | Set-Content $stateFile
}

function Kill-OCRProcess {
    Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'python.exe' -and $_.CommandLine -match 'full_ocr_new\.py'
    } | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Start-Sleep 2
    }
}

function Start-PythonScript($scriptName) {
    $scriptPath = Join-Path $tempDir $scriptName
    Start-Process -FilePath 'python' -ArgumentList "-X utf8 `"$scriptPath`"" -WorkingDirectory $tempDir -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -WindowStyle Hidden
}

switch ($state.stage) {
    'wait_jicha8' {
        # Check if 稽查8 progress file shows 完整
        $pj = Join-Path $tempDir 'output_new\稽查8\_progress.json'
        if (Test-Path $pj) {
            $prog = Get-Content $pj -Raw -Encoding UTF8 | ConvertFrom-Json
            $d = $prog.done.Count
            $t = $prog.total
            # 116/118 = done (2 skipped). Also check >= 98% as fallback.
            if ($d -ge ($t - 2) -or ($logText -match 'DONE .*稽查')) {
                Kill-OCRProcess
                Start-PythonScript 'ocr_drg2025.py'
                Save-State 'drg2025'
                "SWITCH: 稽查8 done ($d/$t) -> DRG2025 started"
            } else {
                "STILL_RUNNING: 稽查8 $d/$t"
            }
        } else {
            "STILL_RUNNING: 稽查8 (no progress file)"
        }
    }
    'drg2025' {
        $pj = Join-Path $tempDir 'output_new\DRG支付2025\_progress.json'
        if (Test-Path $pj) {
            $prog = Get-Content $pj -Raw -Encoding UTF8 | ConvertFrom-Json
            $d = $prog.done.Count
            $t = $prog.total
            if ($d -ge ($t - 2)) {
                Kill-OCRProcess
                Start-PythonScript 'ocr_retry_pages.py'
                Save-State 'retry'
                "SWITCH: DRG2025 done ($d/$t) -> retry started"
            } else {
                "STILL_RUNNING: DRG2025 $d/$t"
            }
        } else {
            "STILL_RUNNING: DRG2025 (no progress file)"
        }
    }
    'retry' {
        if ($logText -match '补跑完成') {
            Save-State 'done'
            "ALL_DONE: 稽查8 p0010/p0013 补跑完成，全部OCR任务结束"
        } else {
            $pj = Join-Path $tempDir 'output_new\稽查8\_progress.json'
            if (Test-Path $pj) {
                $prog = Get-Content $pj -Raw -Encoding UTF8 | ConvertFrom-Json
                $d = $prog.done.Count
                $t = $prog.total
                "STILL_RUNNING: retry phase (稽查8 $d/$t)"
            } else {
                'STILL_RUNNING: retry (ocr_retry_pages.py)'
            }
        }
    }
    'done' { 'ALREADY_DONE' }
    default { "UNKNOWN: $($state.stage)" }
}

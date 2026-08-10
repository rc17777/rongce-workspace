$ErrorActionPreference = "Continue"

Write-Host "=== C: Drive Status ===" -ForegroundColor Cyan
$drive = Get-PSDrive C
Write-Host "Used: $([math]::Round($drive.Used/1GB,1))GB | Free: $([math]::Round($drive.Free/1GB,1))GB"

# Scan cache dirs
$dirs = [ordered]@{
    "User Temp"="$env:TEMP"
    "Windows Temp"="C:\Windows\Temp"
    "Prefetch"="C:\Windows\Prefetch"
    "WinUpdate"="C:\Windows\SoftwareDistribution\Download"
    "npm Cache"="$env:LOCALAPPDATA\npm-cache"
    "pip Cache"="$env:LOCALAPPDATA\pip\cache"
}

Write-Host "`n=== Scanning Caches ===" -ForegroundColor Cyan
$total = 0
foreach ($name in $dirs.Keys) {
    $p = $dirs[$name]
    if (Test-Path $p) {
        $items = Get-ChildItem $p -Recurse -ErrorAction SilentlyContinue
        $s = ($items | Measure-Object -Property Length -Sum).Sum
        if ($s -gt 0) {
            $mb = [math]::Round($s/1MB, 1)
            $total += $s
            Write-Host "  $name : $mb MB" -ForegroundColor Yellow
        } else {
            Write-Host "  $name : 0 MB" -ForegroundColor DarkGray
        }
    }
}
Write-Host "Total scannable: $([math]::Round($total/1MB,1)) MB" -ForegroundColor Green

# Recycle bin
Write-Host "`n=== Recycle Bin ===" -ForegroundColor Cyan
try {
    $rb = Get-ChildItem 'C:\$Recycle.Bin' -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
    $rbMB = [math]::Round($rb.Sum/1MB, 1)
    Write-Host "Recycle Bin: $rbMB MB" -ForegroundColor Yellow
} catch {
    Write-Host "Recycle Bin: access denied" -ForegroundColor DarkGray
}

# Cleanup
Write-Host "`n=== Cleaning ===" -ForegroundColor Cyan
$cutoff = (Get-Date).AddHours(-24)

# User Temp (>24h old files)
$cleaned = 0
if (Test-Path $env:TEMP) {
    Get-ChildItem $env:TEMP -Recurse -ErrorAction SilentlyContinue | Where-Object { 
        $_.LastWriteTime -lt $cutoff -and !$_.PSIsContainer 
    } | ForEach-Object {
        try { Remove-Item $_.FullName -Force -ErrorAction Stop; $script:cleaned += $_.Length } catch {}
    }
}
Write-Host "User Temp (>24h): $([math]::Round($cleaned/1MB,1)) MB removed" -ForegroundColor Green

# Windows Temp
$cleaned2 = 0
if (Test-Path "C:\Windows\Temp") {
    Get-ChildItem "C:\Windows\Temp" -Recurse -ErrorAction SilentlyContinue | Where-Object { 
        $_.LastWriteTime -lt $cutoff -and !$_.PSIsContainer 
    } | ForEach-Object {
        try { Remove-Item $_.FullName -Force -ErrorAction Stop; $script:cleaned2 += $_.Length } catch {}
    }
}
Write-Host "Windows Temp (>24h): $([math]::Round($cleaned2/1MB,1)) MB removed" -ForegroundColor Green

# WinUpdate cache
$cleaned3 = 0
$wu = "C:\Windows\SoftwareDistribution\Download"
if (Test-Path $wu) {
    Get-ChildItem $wu -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        try { $script:cleaned3 += $_.Length; Remove-Item $_.FullName -Recurse -Force -ErrorAction Stop } catch {}
    }
}
Write-Host "WinUpdate Cache: $([math]::Round($cleaned3/1MB,1)) MB removed" -ForegroundColor Green

# Prefetch
$cleaned4 = 0
if (Test-Path "C:\Windows\Prefetch") {
    Get-ChildItem "C:\Windows\Prefetch" -File -ErrorAction SilentlyContinue | ForEach-Object {
        try { $script:cleaned4 += $_.Length; Remove-Item $_.FullName -Force -ErrorAction Stop } catch {}
    }
}
Write-Host "Prefetch: $([math]::Round($cleaned4/1MB,1)) MB removed" -ForegroundColor Green

# pip cache
try {
    $null = pip cache purge 2>&1
    Write-Host "pip Cache: purged" -ForegroundColor Green
} catch {
    Write-Host "pip Cache: skip" -ForegroundColor DarkGray
}

# npm cache verify
try {
    $null = npm cache verify 2>&1
    Write-Host "npm Cache: verified" -ForegroundColor Green
} catch {
    Write-Host "npm Cache: skip" -ForegroundColor DarkGray
}

# disk cleanup tool (cleanmgr - basic)
try {
    Start-Process cleanmgr -ArgumentList "/sagerun:1" -NoNewWindow -Wait -ErrorAction SilentlyContinue
} catch {}

# Final stats
$drive2 = Get-PSDrive C
Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Before: $([math]::Round($drive.Used/1GB,1))GB used | $([math]::Round($drive.Free/1GB,1))GB free" -ForegroundColor Gray
Write-Host "After:  $([math]::Round($drive2.Used/1GB,1))GB used | $([math]::Round($drive2.Free/1GB,1))GB free" -ForegroundColor Green
Write-Host "Freed:  $([math]::Round(($drive.Used - $drive2.Used)/1MB,1)) MB" -ForegroundColor Yellow

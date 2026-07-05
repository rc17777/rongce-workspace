# pre-commit-check.ps1 - Git commit safety scan
# Usage: powershell -File scripts\pre-commit-check.ps1

$ErrorActionPreference = "Stop"
$workspace = $PSScriptRoot | Split-Path -Parent
$issues = @()

Write-Host "=== Rongce Workspace Pre-Commit Check ===" -ForegroundColor Cyan

# 1. Check for sensitive files in staging
Write-Host "[1/5] Checking sensitive files..."
$staged = git -C $workspace diff --cached --name-only 2>$null
if ($LASTEXITCODE -ne 0) {
    $staged = git -C $workspace ls-files 2>$null
}

$sensitivePatterns = @(
    '.env',
    'secrets/',
    '*credentials*.json',
    '*apikey*.json',
    '*.pem',
    '*.key',
    '*.p12',
    '*.pfx'
)

if ($staged) {
    foreach ($file in $staged) {
        foreach ($pattern in $sensitivePatterns) {
            if ($file -like $pattern) {
                $issues += "BLOCKED: Sensitive file staged: $file"
            }
        }
    }

    $envFiles = $staged | Where-Object { $_ -match '\.env$' -and $_ -notmatch '\.env\.example$' }
    if ($envFiles) {
        $issues += "BLOCKED: .env file staged: $envFiles"
    }
}

# 2. Scan for API key patterns in staged files
Write-Host "[2/5] Scanning for API key patterns..."
# Simplified patterns to avoid PowerShell quoting issues
$apiKeyPatterns = @(
    'sk-[a-zA-Z0-9]{32,}',
    'api.key.*[A-Za-z0-9]{32,}',
    'GEMINI_API_KEY'
)

if ($staged) {
    foreach ($file in $staged) {
        $fullPath = Join-Path $workspace $file
        if (-not (Test-Path $fullPath)) { continue }
        
        $ext = [System.IO.Path]::GetExtension($file)
        if ($ext -in '.png','.jpg','.jpeg','.gif','.pdf','.7z','.zip','.exe','.dll','.skill') { continue }
        
        try {
            $content = Get-Content $fullPath -Raw -ErrorAction Stop
        } catch {
            continue
        }
        if (-not $content) { continue }
        
        foreach ($pattern in $apiKeyPatterns) {
            if ($content -match $pattern) {
                # Skip .env.example
                if ($file -eq '.env.example') { continue }
                $issues += "WARNING: Possible API key in: $file (matched pattern: $pattern)"
                break
            }
        }
    }
}

# 3. Check .skill package files
Write-Host "[3/5] Checking .skill files..."
if ($staged) {
    $skillFiles = $staged | Where-Object { $_ -like '*.skill' }
    if ($skillFiles) {
        $issues += "WARNING: .skill package files staged (use source folders instead): $skillFiles"
    }
}

# 4. Check large files (>50MB)
Write-Host "[4/5] Checking large files..."
if ($staged) {
    foreach ($file in $staged) {
        $fullPath = Join-Path $workspace $file
        if (Test-Path $fullPath) {
            $sizeMB = (Get-Item $fullPath).Length / 1MB
            if ($sizeMB -gt 50) {
                $issues += "WARNING: Large file (>50MB): $file ($([math]::Round($sizeMB,1)) MB)"
            }
        }
    }
}

# 5. Verify skill folders have SKILL.md
Write-Host "[5/5] Checking skill integrity..."
$skillDirs = Get-ChildItem (Join-Path $workspace "skills") -Directory -ErrorAction SilentlyContinue
foreach ($dir in $skillDirs) {
    $skillMd = Join-Path $dir.FullName "SKILL.md"
    if (-not (Test-Path $skillMd)) {
        $issues += "WARNING: Missing SKILL.md in skills/$($dir.Name)"
    }
}

# Output results
Write-Host ""
Write-Host "=== Results ==="
if ($issues.Count -eq 0) {
    Write-Host "PASS: All checks passed. Safe to commit." -ForegroundColor Green
    exit 0
} else {
    Write-Host "FAIL: Found $($issues.Count) issue(s):" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "Commit blocked. Fix issues and retry." -ForegroundColor Red
    exit 1
}

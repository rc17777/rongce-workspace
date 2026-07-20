# Pagefile migration: remove C: pagefile entry, keep D: (system managed)
# Requires admin. ASCII-only to avoid encoding issues.
$ErrorActionPreference = 'Continue'
Start-Transcript -Path "C:\Users\scrccpa\pagefile_migration.log" -Force

$cs = Get-CimInstance Win32_ComputerSystem
if ($cs.AutomaticManagedPagefile) {
    Set-CimInstance -InputObject $cs -Property @{AutomaticManagedPagefile=$false}
    Write-Host "Disabled automatic pagefile management"
}

Get-CimInstance Win32_PageFileSetting | ForEach-Object {
    $n = $_.Name
    if ([string]::IsNullOrWhiteSpace($n) -or $n -like 'C:*') {
        Write-Host "Removing pagefile entry: [$n]"
        Remove-CimInstance -InputObject $_
    }
}

$d = Get-CimInstance Win32_PageFileSetting | Where-Object { $_.Name -like 'D:*' }
if (-not $d) {
    New-CimInstance -ClassName Win32_PageFileSetting -Property @{Name='D:\pagefile.sys'; InitialSize=[uint32]0; MaximumSize=[uint32]0} | Out-Null
    Write-Host "Created D:\pagefile.sys (system managed)"
} else {
    Write-Host "D: pagefile already exists: $($d.Name)"
}

Write-Host ""
Write-Host "=== Final pagefile settings ==="
Get-CimInstance Win32_PageFileSetting | Format-Table Name, InitialSize, MaximumSize -AutoSize

Write-Host ""
Write-Host "DONE. Takes effect after reboot. C: will free ~2.4GB."
Stop-Transcript
Read-Host "Press Enter to close"

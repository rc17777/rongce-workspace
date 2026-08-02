$files = Get-ChildItem "$env:USERPROFILE\.openclaw\workspace\temp_ocr\output_new\*\_progress.json"
foreach ($f in $files) {
    $j = Get-Content $f.FullName -Raw | ConvertFrom-Json
    $d = $j.done.Count
    $pct = [math]::Round($d/$j.total*100, 1)
    Write-Host ("  " + $j.label + ": " + $d + "/" + $j.total + " (" + $pct + "%)")
}

$log = Get-Content "$env:USERPROFILE\.openclaw\workspace\temp_ocr\ocr_log.txt" -Tail 1
Write-Host ("Last line: " + $log)

$allLines = Get-Content "$env:USERPROFILE\.openclaw\workspace\temp_ocr\ocr_log.txt"
$okCount = 0
foreach ($line in $allLines) {
    if ($line -match "OK" -and ($line -match "08-02 15:0" -or $line -match "08-02 14:5[5-9]" -or $line -match "08-02 15:1[0-5]")) {
        $okCount++
    }
}
Write-Host ("OK lines in last 15 min: " + $okCount)

# Get current active book from log
$tail3 = Get-Content "$env:USERPROFILE\.openclaw\workspace\temp_ocr\ocr_log.txt" -Tail 3
Write-Host "=== Last 3 lines ==="
foreach ($line in $tail3) {
    Write-Host $line
}
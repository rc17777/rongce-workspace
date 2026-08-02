$files = Get-ChildItem "$env:USERPROFILE\.openclaw\workspace\temp_ocr\output_new\*\_progress.json"
foreach ($f in $files) {
    Write-Host "=== $($f.Directory.Name) ==="
    Get-Content $f.FullName
    Write-Host ""
}
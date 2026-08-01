$files = Get-ChildItem "C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\*\_progress.json"
foreach ($f in $files) {
    Write-Host "=== $($f.Directory.Name) ==="
    Get-Content $f.FullName
}
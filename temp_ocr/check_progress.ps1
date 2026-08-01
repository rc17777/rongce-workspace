$dirs = Get-ChildItem "C:\Users\scrccpa\.openclaw\workspace\temp_ocr\output_new\" -Directory
foreach ($d in $dirs) {
    $pf = Join-Path $d.FullName "_progress.json"
    if (Test-Path $pf) {
        $c = Get-Content $pf -Raw
        Write-Host ">>> $($d.Name) >>>"
        Write-Host $c
    }
}
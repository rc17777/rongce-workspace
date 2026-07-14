try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:18789/' -TimeoutSec 5 -UseBasicParsing
    Write-Output "Status: $($r.StatusCode)"
    Write-Output "Content-Type: $($r.Headers['Content-Type'])"
    Write-Output "Length: $($r.Content.Length)"
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}

try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:18789/api/status' -TimeoutSec 5 -UseBasicParsing
    Write-Output "API Status: $($r.StatusCode)"
    Write-Output "API Content: $($r.Content)"
} catch {
    Write-Output "API Error: $($_.Exception.Message)"
}

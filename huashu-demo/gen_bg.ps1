$body = @{
    model = 'gpt-image-2'
    messages = @(
        @{
            role = 'user'
            content = 'Generate a classical dark Chinese ink-wash background with jade-green and gold tones. 16:9 aspect ratio. No text. Serene, artisan mood.'
        }
    )
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri 'https://cbwyy.top/v1/chat/completions' `
        -Method Post `
        -Headers @{'Authorization'='Bearer sk-KVp2E6u9FnnRA3BQxSNvbWKW6zd2JsDQa8YlmR4ZxGtVsXIQ'; 'Content-Type'='application/json'} `
        -Body $body `
        -TimeoutSec 120

    $response | ConvertTo-Json -Depth 10 > C:\Users\scrccpa\.openclaw\workspace\huashu-demo\output\img_response.json
    Write-Host "OK - response saved"
} catch {
    Write-Host "Error: $_"
    $_.Exception | Format-List -Force
}

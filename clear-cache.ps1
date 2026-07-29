# 清除浏览器缓存并重启 OpenClaw 的脚本
# 运行后 DeepSeek 新密钥应该生效

Write-Host "=== 清除 OpenClaw 浏览器缓存 ===" -ForegroundColor Cyan

# 1. 关闭 Chrome/Edge 中所有 openclaw 页面
$openclawProcesses = Get-Process | Where-Object { 
    $_.ProcessName -match "chrome|edge|msedge" -and 
    $_.MainWindowTitle -match "OpenClaw|127.0.0.1:18789" 
}
if ($openclawProcesses) {
    Write-Host "关闭 OpenClaw 浏览器标签..." -ForegroundColor Yellow
    $openclawProcesses | ForEach-Object { $_.CloseMainWindow() | Out-Null }
    Start-Sleep -Seconds 2
}

# 2. 清除 Local Storage
$chromeLocalStorage = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Local Storage"
$edgeLocalStorage = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Local Storage"

foreach ($path in @($chromeLocalStorage, $edgeLocalStorage)) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Filter "*openclaw*" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "已清除: $path" -ForegroundColor Green
    }
}

# 3. 清除 IndexedDB
$chromeIndexedDB = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\IndexedDB"
$edgeIndexedDB = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\IndexedDB"

foreach ($path in @($chromeIndexedDB, $edgeIndexedDB)) {
    if (Test-Path $path) {
        Get-ChildItem -Path $path -Filter "*127.0.0.1*18789*" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "已清除 IndexedDB: $path" -ForegroundColor Green
    }
}

Write-Host "`n=== 缓存清除完成 ===" -ForegroundColor Cyan
Write-Host "请重新打开浏览器访问 http://127.0.0.1:18789" -ForegroundColor Yellow
Write-Host "然后选择 DeepSeek 模型测试" -ForegroundColor Yellow

# 4. 验证配置文件
Write-Host "`n=== 验证当前配置 ===" -ForegroundColor Cyan
$configPath = "$env:USERPROFILE\.openclaw\openclaw.json"
if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    $deepseekKey = $config.models.providers.deepseek.apiKey
    if ($deepseekKey -eq "sk-7d5037d1d1c145f5b9ef928fcd696e5c") {
        Write-Host "✅ 配置文件密钥正确: sk-7d5..." -ForegroundColor Green
    } else {
        Write-Host "❌ 配置文件密钥不匹配!" -ForegroundColor Red
        Write-Host "当前: $deepseekKey" -ForegroundColor Red
    }
}

Write-Host "`n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

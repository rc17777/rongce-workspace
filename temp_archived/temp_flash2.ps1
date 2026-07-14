Write-Host "=== 闪窗嫌疑分析 ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔴 嫌疑人1号: LenovoVantage SmartDisplayAddin.exe" -ForegroundColor Red
Write-Host "  崩溃频率: 每5-8分钟一次"
Write-Host "  证据: 事件日志中反复出现 c0000005 (空指针访问)"
Write-Host "  模块: SESmartWireless.dll (智能无线模块)"
Write-Host "  现象: 崩溃 -> 弹出'程序已停止工作'对话框 -> 自愈/重启 -> 又崩溃"
Write-Host ""

Write-Host "🟡 嫌疑人2号: 融策Agent巡检 (patrol.ps1)" -ForegroundColor Yellow
Write-Host "  频率: 每5分钟执行"
Write-Host "  上次运行: 00:39:39"
Write-Host "  命令: powershell.exe -WindowStyle Hidden -File patrol.ps1"
Write-Host "  WindowStyle Hidden 通常不闪窗，但不能100%保证"
Write-Host ""

Write-Host "🟡 嫌疑人3号: WPS Update" -ForegroundColor Yellow
Write-Host "  上次运行: 00:39:xx"
Write-Host "  WPS后台更新偶尔会弹窗"
Write-Host ""

Write-Host "=== LenovoVantage 崩溃详细时间线 ===" -ForegroundColor Cyan
Get-WinEvent -FilterHashtable @{LogName='Application'; Level=2; ProviderName='.NET Runtime'; StartTime=(Get-Date).AddHours(-6)} -MaxEvents 30 -ErrorAction SilentlyContinue | ForEach-Object {
    $msg = $_.Message
    if ($msg -match 'LenovoVantage') {
        Write-Host "[$($_.TimeCreated)] CRASH: SmartDisplayAddin"
    } elseif ($msg -match 'nhi') {
        # skip
    } else {
        $short = $msg.Substring(0, [Math]::Min(80, $msg.Length))
        Write-Host "[$($_.TimeCreated)] $short"
    }
}

Write-Host ""
Write-Host "=== patrol.ps1 内容 (前30行) ===" -ForegroundColor Cyan
$patrolPath = "D:\openclaw-workspace\projects\data-analysis-agent\patrol.ps1"
if (Test-Path $patrolPath) {
    Get-Content $patrolPath -TotalCount 30 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "patrol.ps1 not found! Task is running phantom script." -ForegroundColor Red
}

Write-Host ""
Write-Host "=== LenovoVantage 服务状态 ===" -ForegroundColor Cyan
Get-Service -Name '*Lenovo*','*Vantage*','*ImController*' -ErrorAction SilentlyContinue | Format-Table Name, Status, StartType
Get-Process -Name '*Lenovo*','*Vantage*','*SmartDisplay*' -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "PID $($_.Id) $($_.ProcessName) - Mem: $([math]::Round($_.WorkingSet64/1MB,0))MB"
}

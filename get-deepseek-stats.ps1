# DeepSeek 使用统计查看脚本
# 运行: powershell -File get-deepseek-stats.ps1

Write-Host "=== DeepSeek 使用统计 ===" -ForegroundColor Cyan
Write-Host ""

# 查看网关日志中的 DeepSeek 调用
Write-Host "从网关日志提取的 DeepSeek 记录:" -ForegroundColor Yellow
$deepseekLogs = Select-String -Path "$env:USERPROFILE\.openclaw\gateway.log" -Pattern "deepseek" -CaseSensitive:$false | Select-Object -Last 20

if ($deepseekLogs) {
    foreach ($log in $deepseekLogs) {
        $line = $log.Line
        # 提取时间戳
        if ($line -match '(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})') {
            $timestamp = $Matches[1]
        }
        
        # 提取状态
        if ($line -match 'billing error|Insufficient Balance') {
            Write-Host "[$timestamp] " -NoNewline
            Write-Host "❌ 余额不足" -ForegroundColor Red
        } elseif ($line -match 'timeout') {
            Write-Host "[$timestamp] " -NoNewline
            Write-Host "⚠️ 超时" -ForegroundColor Yellow
        } elseif ($line -match 'fallback') {
            Write-Host "[$timestamp] " -NoNewline
            Write-Host "🔄 Fallback到Kimi" -ForegroundColor Green
        } elseif ($line -match 'model-fallback.*candidate_succeeded') {
            # 跳过重复的成功记录
        } else {
            Write-Host "[$timestamp] $line" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "未找到 DeepSeek 调用记录" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== 账户余额状态 ===" -ForegroundColor Cyan

# 查询当前余额
try {
    $response = Invoke-RestMethod -Uri "https://api.deepseek.com/user/balance" -Headers @{"Authorization"="Bearer sk-7d5037d1d1c145f5b9ef928fcd696e5c"} -Method GET -ErrorAction SilentlyContinue
    if ($response.is_available -eq $false) {
        Write-Host "账户状态: " -NoNewline
        Write-Host "❌ 欠费/不可用" -ForegroundColor Red
    } else {
        Write-Host "账户状态: " -NoNewline
        Write-Host "✅ 正常" -ForegroundColor Green
    }
    
    foreach ($info in $response.balance_infos) {
        Write-Host "货币: $($info.currency)" 
        Write-Host "总余额: $($info.total_balance)"
        Write-Host "赠送余额: $($info.granted_balance)"
        Write-Host "充值余额: $($info.topped_up_balance)"
    }
} catch {
    Write-Host "无法查询余额: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 使用建议 ===" -ForegroundColor Cyan
Write-Host "1. DeepSeek 平台不提供详细API日志" -ForegroundColor White
Write-Host "2. 如需监控未来使用，建议开启详细日志记录" -ForegroundColor White
Write-Host "3. 当前配置中 DeepSeek 是 fallback 模型，主模型是 Kimi" -ForegroundColor White
Write-Host "4. 审计数据分析师 agent 专门使用 DeepSeek，可能是主要消耗来源" -ForegroundColor White

#!/usr/bin/env node
/**
 * API Token 监控脚本
 * 记录所有模型调用的 Token 使用情况
 * 用法: node token-monitor.js log < json-data
 *       node token-monitor.js today
 */

const fs = require('fs');
const path = require('path');

const LOG_FILE = path.join(__dirname, 'token-monitor.log');
const CSV_FILE = path.join(__dirname, 'token-usage.csv');

// 初始化 CSV 文件
function initCSV() {
    if (!fs.existsSync(CSV_FILE)) {
        fs.writeFileSync(CSV_FILE, 'timestamp,provider,model,input_tokens,output_tokens,cache_read,cache_write,total_tokens,cost_usd,cost_cny,session_id,status\n');
    }
}

// 记录一次 API 调用
function logAPICall(data) {
    const {
        timestamp = new Date().toISOString(),
        provider,
        model,
        inputTokens = 0,
        outputTokens = 0,
        cacheRead = 0,
        cacheWrite = 0,
        totalTokens = inputTokens + outputTokens,
        costUSD = 0,
        costCNY = 0,
        sessionId = '',
        status = 'success'
    } = data;

    // 追加到 CSV
    const line = `${timestamp},${provider},${model},${inputTokens},${outputTokens},${cacheRead},${cacheWrite},${totalTokens},${costUSD},${costCNY},${sessionId},${status}\n`;
    fs.appendFileSync(CSV_FILE, line);

    // 同时记录到日志
    const logEntry = `[${timestamp}] ${provider}/${model}: ${totalTokens} tokens (in:${inputTokens}, out:${outputTokens}) | Cost: $${costUSD} | Status: ${status}\n`;
    fs.appendFileSync(LOG_FILE, logEntry);
}

// 获取今日统计
function getTodayStats() {
    if (!fs.existsSync(CSV_FILE)) return null;
    
    const today = new Date().toISOString().split('T')[0];
    const lines = fs.readFileSync(CSV_FILE, 'utf8').split('\n').slice(1); // 跳过表头
    
    let stats = {
        totalCalls: 0,
        totalTokens: 0,
        totalInput: 0,
        totalOutput: 0,
        totalCostUSD: 0,
        totalCostCNY: 0,
        byModel: {}
    };

    for (const line of lines) {
        if (!line.trim()) continue;
        const [timestamp, provider, model, input, output, cacheRead, cacheWrite, total, costUSD, costCNY, sessionId, status] = line.split(',');
        
        if (timestamp.startsWith(today)) {
            stats.totalCalls++;
            stats.totalTokens += parseInt(total) || 0;
            stats.totalInput += parseInt(input) || 0;
            stats.totalOutput += parseInt(output) || 0;
            stats.totalCostUSD += parseFloat(costUSD) || 0;
            stats.totalCostCNY += parseFloat(costCNY) || 0;
            
            const key = `${provider}/${model}`;
            if (!stats.byModel[key]) {
                stats.byModel[key] = { calls: 0, tokens: 0 };
            }
            stats.byModel[key].calls++;
            stats.byModel[key].tokens += parseInt(total) || 0;
        }
    }

    return stats;
}

// 主函数
function main() {
    initCSV();
    
    const command = process.argv[2];
    
    if (command === 'log') {
        // 从 stdin 读取 JSON 数据
        let data = '';
        process.stdin.on('data', chunk => data += chunk);
        process.stdin.on('end', () => {
            try {
                const parsed = JSON.parse(data);
                logAPICall(parsed);
                console.log('Logged successfully');
            } catch (e) {
                console.error('Failed to parse input:', e.message);
                process.exit(1);
            }
        });
    } else if (command === 'today') {
        const stats = getTodayStats();
        if (stats) {
            console.log('=== 今日 API 使用统计 ===');
            console.log(`总调用次数: ${stats.totalCalls}`);
            console.log(`总 Token 数: ${stats.totalTokens.toLocaleString()}`);
            console.log(`  - 输入: ${stats.totalInput.toLocaleString()}`);
            console.log(`  - 输出: ${stats.totalOutput.toLocaleString()}`);
            console.log(`总费用: $${stats.totalCostUSD.toFixed(4)} / ¥${stats.totalCostCNY.toFixed(2)}`);
            console.log('\n按模型统计:');
            for (const [model, data] of Object.entries(stats.byModel)) {
                console.log(`  ${model}: ${data.calls} 次, ${data.tokens.toLocaleString()} tokens`);
            }
        } else {
            console.log('暂无数据');
        }
    } else {
        console.log('Usage:');
        console.log('  node token-monitor.js log < json-data');
        console.log('  node token-monitor.js today');
    }
}

main();

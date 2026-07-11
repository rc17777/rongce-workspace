# Token 监控脚本
# 追踪各模型每日 token 消耗

import json
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

AGENTS_DIR = Path(os.path.expanduser("~/.openclaw/agents"))
LOG_FILE = Path(os.path.expanduser("~/.openclaw/workspace-main/token-monitor.log"))
REPORT_FILE = Path(os.path.expanduser("~/.openclaw/workspace-main/token-daily-report.md"))

MODEL_NAMES = {
    "deepseek": "DeepSeek",
    "kimi-coding": "Kimi",
    "dashscope": "Qwen",
    "openai": "OpenAI",
}

def get_model_name(provider, model_id):
    base = MODEL_NAMES.get(provider, provider)
    return f"{base} ({model_id})"

def get_token_usage(target_date):
    """统计指定日期的 token 使用量"""
    start = datetime.strptime(target_date, "%Y-%m-%d")
    end = start + timedelta(days=1)
    
    results = defaultdict(lambda: {
        "provider": "",
        "model": "",
        "input": 0,
        "output": 0,
        "cache_read": 0,
        "cache_write": 0,
        "count": 0,
    })
    
    # 遍历所有 jsonl 文件
    for jsonl_file in AGENTS_DIR.rglob("*.jsonl"):
        mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
        if not (start <= mtime < end):
            continue
        
        try:
            with open(jsonl_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if '"usage"' not in line:
                        continue
                    
                    # 提取 provider
                    provider_match = re.search(r'"provider":"([^"]+)"', line)
                    provider = provider_match.group(1) if provider_match else "unknown"
                    
                    # 提取 model
                    model_match = re.search(r'"model":"([^"]+)"', line)
                    model = model_match.group(1) if model_match else "unknown"
                    
                    # 提取 usage 数值
                    input_match = re.search(r'"input":(\d+)', line)
                    output_match = re.search(r'"output":(\d+)', line)
                    cache_read_match = re.search(r'"cacheRead":(\d+)', line)
                    cache_write_match = re.search(r'"cacheWrite":(\d+)', line)
                    
                    key = f"{provider}|{model}"
                    results[key]["provider"] = provider
                    results[key]["model"] = model
                    results[key]["input"] += int(input_match.group(1)) if input_match else 0
                    results[key]["output"] += int(output_match.group(1)) if output_match else 0
                    results[key]["cache_read"] += int(cache_read_match.group(1)) if cache_read_match else 0
                    results[key]["cache_write"] += int(cache_write_match.group(1)) if cache_write_match else 0
                    results[key]["count"] += 1
        except Exception as e:
            print(f"Warning: 读取 {jsonl_file} 出错: {e}")
            continue
    
    return dict(results)

def write_daily_report(target_date):
    """生成每日报告"""
    usage = get_token_usage(target_date)
    
    report_lines = [
        f"# Token 使用报告 - {target_date}",
        "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    
    total_tokens = 0
    total_calls = 0
    
    for key in sorted(usage.keys()):
        data = usage[key]
        tokens = data["input"] + data["output"] + data["cache_read"]
        total_tokens += tokens
        total_calls += data["count"]
        
        report_lines.extend([
            f"## {get_model_name(data['provider'], data['model'])}",
            "",
            f"- Provider: `{data['provider']}`",
            f"- 调用次数: {data['count']}",
            f"- Input: {data['input']:,} tokens",
            f"- Output: {data['output']:,} tokens",
            f"- Cache Read: {data['cache_read']:,} tokens",
            f"- Cache Write: {data['cache_write']:,} tokens",
            f"- **合计: {tokens:,} tokens**",
            "",
        ])
    
    report_lines.extend([
        "---",
        "",
        "## 总计",
        "",
        f"- **总调用次数: {total_calls}**",
        f"- **总 Token 数: {total_tokens:,}**",
        "",
    ])
    
    # 异常检测
    ALERT_THRESHOLD = 500000  # 50万 tokens
    if total_tokens > ALERT_THRESHOLD:
        report_lines.extend([
            "⚠️ **异常提醒**: 昨日总消耗超过 500K tokens，建议检查是否有异常调用",
            "",
        ])
    
    report_text = "\n".join(report_lines)
    
    # 写入报告文件
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    # 追加到日志
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{target_date} | Total: {total_tokens:,} tokens | Calls: {total_calls}\n")
    
    print(f"✅ 报告已保存: {REPORT_FILE}")
    print(f"📊 总消耗: {total_tokens:,} tokens ({total_calls} 次调用)")
    
    return report_text

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"🔍 统计日期: {target}")
    report = write_daily_report(target)
    print("\n" + "="*50)
    print(report)

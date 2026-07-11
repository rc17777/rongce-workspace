#!/usr/bin/env python3
"""
DeepSeek Token 消耗分析器
"""
import csv
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 读取 cost 文件 ──
cost_rows = list(csv.DictReader(Path("C:/Users/scrccpa/Desktop/cost-2026-6.csv").open("r", encoding="utf-8-sig")))
# ── 读取 amount 文件 ──
amount_rows = list(csv.DictReader(Path("C:/Users/scrccpa/Desktop/amount-2026-6.csv").open("r", encoding="utf-8-sig")))

# 汇总每日费用
daily_cost = defaultdict(lambda: {"v4pro": 0.0, "flash": 0.0, "total": 0.0})
for r in cost_rows:
    d = r["utc_date"]
    model = r["model"]
    c = float(r["cost"])
    if "v4-pro" in model:
        daily_cost[d]["v4pro"] += c
    elif "v4-flash" in model:
        daily_cost[d]["flash"] += c
    daily_cost[d]["total"] += c

# 汇总每日 token 用量（按 model + type）
daily_tokens = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for r in amount_rows:
    d = r["utc_date"]
    model = r["model"]
    ttype = r["type"]
    amt = int(r["amount"]) if r["amount"] else 0
    daily_tokens[d][model][ttype] += amt

# 按日期排序
all_dates = sorted(set(daily_cost.keys()) | set(daily_tokens.keys()))

print("=" * 90)
print("DeepSeek Token 消耗日报 (2026年6月)")
print("=" * 90)
print(f"{'日期':<12} {'V4 Pro(¥)':>12} {'Flash(¥)':>12} {'合计(¥)':>12} {'V4-Pro Token':>14} {'Flash Token':>14} {'请求数':>8}")
print("-" * 90)

total_cost = 0.0
for d in all_dates:
    c = daily_cost.get(d, {})
    t = daily_tokens.get(d, {})
    
    v4pro_cost = c.get("v4pro", 0)
    flash_cost = c.get("flash", 0)
    day_total = c.get("total", 0)
    total_cost += day_total
    
    # Token 统计
    v4pro_tokens = sum(t.get("deepseek-v4-pro", {}).values())
    flash_tokens = sum(t.get("deepseek-v4-flash", {}).values())
    
    # 请求数
    v4_req = t.get("deepseek-v4-pro", {}).get("request_count", 0)
    flash_req = t.get("deepseek-v4-flash", {}).get("request_count", 0)
    total_req = v4_req + flash_req
    
    marker = ""
    if day_total > 300:
        marker = " 🔥🔥🔥"
    elif day_total > 100:
        marker = " 🔥🔥"
    elif day_total > 50:
        marker = " 🔥"
    
    print(f"{d:<12} {v4pro_cost:>12.2f} {flash_cost:>12.2f} {day_total:>12.2f} {v4pro_tokens:>14,} {flash_tokens:>14,} {total_req:>8,}{marker}")

print("-" * 90)
print(f"{'总计':<12} {'':>12} {'':>12} {total_cost:>12.2f}")
print()

# ── 找出异常峰值日 ──
print("=" * 90)
print("异常峰值分析")
print("=" * 90)

peak_dates = [d for d in all_dates if daily_cost.get(d, {}).get("total", 0) > 100]
for d in peak_dates:
    c = daily_cost.get(d, {})
    t = daily_tokens.get(d, {})
    print(f"\n📅 {d} — 费用 ¥{c.get('total', 0):.2f}")
    
    for model in ["deepseek-v4-pro", "deepseek-v4-flash"]:
        if model not in t:
            continue
        td = t[model]
        req = td.get("request_count", 0)
        out = td.get("output_tokens", 0)
        miss = td.get("input_cache_miss_tokens", 0)
        hit = td.get("input_cache_hit_tokens", 0)
        total_t = hit + miss + out
        
        print(f"  [{model}]")
        print(f"    请求数: {req:,} 次")
        print(f"    Cache Hit:  {hit:>15,} tokens")
        print(f"    Cache Miss: {miss:>15,} tokens")
        print(f"    Output:     {out:>15,} tokens")
        print(f"    合计:       {total_t:>15,} tokens")
        
        if req > 0:
            avg_out_per_req = out / req
            print(f"    平均每请求输出: {avg_out_per_req:,.0f} tokens")

print()

# ── 关键指标 ──
print("=" * 90)
print("关键指标汇总")
print("=" * 90)

# 找出最大单日
max_day = max(all_dates, key=lambda d: daily_cost.get(d, {}).get("total", 0))
max_cost = daily_cost[max_day]["total"]

# 6月1-17日均值
early_dates = [d for d in all_dates if d <= "2026-06-17"]
early_avg = sum(daily_cost.get(d, {}).get("total", 0) for d in early_dates) / len(early_dates) if early_dates else 0

# 6月18-25日均值
late_dates = [d for d in all_dates if "2026-06-18" <= d <= "2026-06-25"]
late_avg = sum(daily_cost.get(d, {}).get("total", 0) for d in late_dates) / len(late_dates) if late_dates else 0

# Flash 占总费用比例
flash_total = sum(daily_cost.get(d, {}).get("flash", 0) for d in all_dates)
pro_total = sum(daily_cost.get(d, {}).get("v4pro", 0) for d in all_dates)

print(f"6月1-17日 日均费用: ¥{early_avg:.2f}")
print(f"6月18-25日 日均费用: ¥{late_avg:.2f}")
print(f"涨幅倍数: {late_avg/early_avg:.1f}x")
print(f"峰值日期: {max_day} (¥{max_cost:.2f})")
print(f"峰值/早期均值: {max_cost/early_avg:.1f}x")
print(f"\n费用结构:")
print(f"  V4 Pro:  ¥{pro_total:.2f} ({pro_total/total_cost*100:.1f}%)")
print(f"  Flash:   ¥{flash_total:.2f} ({flash_total/total_cost*100:.1f}%)")
print(f"\n6月总费用: ¥{total_cost:.2f}")

# 计算6月24日Flash的详细情况
d = "2026-06-24"
if d in daily_tokens:
    t = daily_tokens[d]["deepseek-v4-flash"]
    req = t.get("request_count", 0)
    miss = t.get("input_cache_miss_tokens", 0)
    out = t.get("output_tokens", 0)
    print(f"\n⚠️  6月24日 Flash 异常警报:")
    print(f"    4.4万次请求，3亿输入token + 9200万输出token")
    print(f"    平均每请求: {miss/req:,.0f} input + {out/req:,.0f} output = {(miss+out)/req:,.0f} tokens")
    print(f"    这远超正常对话模式，疑似批量脚本或循环调用")

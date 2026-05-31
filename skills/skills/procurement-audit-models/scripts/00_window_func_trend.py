"""技能② OVER/PARTITION BY窗口函数 → 中标趋势/累计分析
来源：泉州医保"SUM+OVER(PARTITION BY ORDER BY)逐层累计"
用途：投标人历史中标金额累计跟踪、异常增长检测
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding='utf-8')


def cumulative_trend(records, entity_key, date_key, value_key, 
                     months_back=24):
    """窗口函数模拟：逐月累计趋势分析
    
    records: [{"投标人":"A","中标日期":"2024-01-15","中标金额":50}, ...]
    
    返回: 每个实体每个月的累计值、环比增长率
    """
    # 解析日期
    for r in records:
        if isinstance(r[date_key], str):
            r["_date"] = datetime.strptime(r[date_key][:10], "%Y-%m-%d")
        else:
            r["_date"] = r[date_key]
    
    # 按月分组
    monthly = defaultdict(lambda: defaultdict(float))
    for r in records:
        entity = r[entity_key]
        month = r["_date"].strftime("%Y-%m")
        monthly[entity][month] += r[value_key]
    
    # 计算逐月累计
    results = []
    for entity, months_data in monthly.items():
        sorted_months = sorted(months_data.keys())
        cumulative = 0
        prev_month_total = 0
        
        for month in sorted_months:
            monthly_total = months_data[month]
            cumulative += monthly_total
            
            growth = ((monthly_total - prev_month_total) / prev_month_total * 100) \
                     if prev_month_total > 0 else None
            
            results.append({
                "实体": entity,
                "月份": month,
                "当月金额": round(monthly_total, 2),
                "累计金额": round(cumulative, 2),
                "环比增长%": round(growth, 1) if growth else None
            })
            
            prev_month_total = monthly_total
    
    results.sort(key=lambda x: (x["实体"], x["月份"]))
    return results


def detect_sudden_spike(records, entity_key, date_key, value_key,
                        spike_threshold=3.0):
    """检测累计金额突然放量
    
    方法: 最近12个月累计 / 前12个月累计 > spike_threshold
    → 标记为异常增长
    """
    entity_data = defaultdict(list)
    for r in records:
        entity_data[r[entity_key]].append({
            "date": r[date_key] if isinstance(r[date_key], datetime) 
                    else datetime.strptime(r[date_key][:10], "%Y-%m-%d"),
            "value": r[value_key]
        })
    
    alerts = []
    for entity, data in entity_data.items():
        data.sort(key=lambda x: x["date"])
        if len(data) < 2:
            continue
        
        # 找到最近12个月和之前12个月的累计
        latest = data[-1]["date"]
        yr_ago = latest - timedelta(days=365)
        
        recent = sum(d["value"] for d in data if d["date"] > yr_ago)
        before = sum(d["value"] for d in data if d["date"] <= yr_ago)
        
        if before > 0:
            ratio = recent / before
            if ratio >= spike_threshold:
                alerts.append({
                    "实体": entity,
                    "前期累计(12个月前)": round(before, 2),
                    "近期累计(最近12月)": round(recent, 2),
                    "放量倍数": round(ratio, 1),
                    "总记录数": len(data),
                    "首次中标": data[0]["date"].strftime("%Y-%m-%d"),
                    "最近中标": data[-1]["date"].strftime("%Y-%m-%d")
                })
    
    alerts.sort(key=lambda x: -x["放量倍数"])
    return alerts


def project_budget_tracker(budgets, expenses):
    """项目预算执行率跟踪（用于工程结算/预算评审）
    
    budgets: [{"项目":"A","预算金额":1000}, ...]
    expenses: [{"项目":"A","日期":"2024-01","支出":50}, ...]
    
    返回: 每个项目的逐月预算执行进度
    """
    budget_map = {b["项目"]: b["预算金额"] for b in budgets}
    
    # 按项目+月份汇总
    monthly_exp = defaultdict(float)
    for e in expenses:
        key = (e["项目"], e["日期"][:7])
        monthly_exp[key] += e["支出"]
    
    results = []
    for (proj, month), exp_total in sorted(monthly_exp.items()):
        budget = budget_map.get(proj, 0)
        exec_rate = (exp_total / budget * 100) if budget > 0 else 0
        results.append({
            "项目": proj,
            "月份": month,
            "当月支出": round(exp_total, 2),
            "预算总额": budget,
            "执行率%": round(exec_rate, 1)
        })
    
    return results


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("窗口函数 — 中标趋势分析 + 异常放量检测")
    print("=" * 60)
    
    # 模拟：投标人3年中标记录
    import random
    random.seed(42)
    
    records = []
    entities = {"四川融策建设": "稳步增长", "成都某建筑": "突然放量", 
                "德阳某咨询": "稳定"}
    
    base = datetime(2024, 1, 1)
    for entity, pattern in entities.items():
        cumul = 0
        for m in range(36):
            date = base + timedelta(days=m*30 + random.randint(0,15))
            
            if pattern == "突然放量" and m >= 30:
                # 最后6个月突然放量3倍
                amount = 50 + random.randint(30, 70)
            elif pattern == "稳步增长":
                amount = 10 + random.randint(5, 15)
            else:
                amount = 20 + random.randint(10, 20)
            
            records.append({
                "投标人": entity,
                "中标日期": date.strftime("%Y-%m-%d"),
                "中标金额": amount
            })
    
    # 逐月累计趋势
    trend = cumulative_trend(records, "投标人", "中标日期", "中标金额")
    
    # 只看最近6个月
    for t in trend:
        if t["月份"] >= "2026-01":
            bar = "█" * int(t["当月金额"] / 3)
            growth = t["环比增长%"] or 0
            spike = " ⚠️" if growth > 50 else ""
            print(f"  {t['实体']:12s} {t['月份']} "
                  f"当月:{t['当月金额']:6.0f} 累计:{t['累计金额']:6.0f} "
                  f"增长:{growth:5.0f}%{spike} {bar}")
    
    # 异常放量检测
    print(f"\n--- 异常放量检测 ---")
    alerts = detect_sudden_spike(records, "投标人", "中标日期", "中标金额",
                                 spike_threshold=1.5)
    for a in alerts:
        print(f"  🔴 {a['实体']}: 前期{a['前期累计(12个月前)']:.0f} → "
              f"近期{a['近期累计(最近12月)']:.0f} "
              f"= {a['放量倍数']}x 放量!")

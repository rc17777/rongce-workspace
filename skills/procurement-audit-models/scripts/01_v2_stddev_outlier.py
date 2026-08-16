"""技能① STDDEV标准差异常检测 — 报价分析升级版
来源：泉州医保"偏离值落在一定范围的记录单独存表分析"
用途：大样本报价的自动化异常标记（比单纯看极差更科学）
"""
import sys, math
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

try:
    import numpy as np
except ImportError:
    print("需要: pip install numpy"); sys.exit(1)


def stddev_outlier(prices, sigma=2.0):
    """基于标准差的异常值检测
    
    prices: 报价列表 [{"投标人":"A","报价":645}, ...]
    sigma: 几倍标准差为阈值（默认2倍）
    
    返回: 标记了异常的列表
    """
    values = np.array([p["报价"] for p in prices])
    mu = np.mean(values)
    std = np.std(values, ddof=1)  # 样本标准差
    
    results = []
    for p in prices:
        z = (p["报价"] - mu) / std if std > 0 else 0
        flag = ""
        if z > sigma:
            flag = f"偏高{abs(z):.1f}σ"
        elif z < -sigma:
            flag = f"偏低{abs(z):.1f}σ"
        
        results.append({
            **p,
            "均值": round(mu, 2),
            "标准差": round(std, 2),
            "Z分数": round(z, 2),
            "标志": flag,
            "百分位": round((np.sum(values <= p["报价"]) / len(values)) * 100, 1)
        })
    
    return results


def group_stddev(items, group_key, value_key, sigma=2.0):
    """分组标准差异常检测（如按项目/标段分组）
    
    items: [{"项目":"P1","投标人":"A","报价":645}, ...]
    group_key: 分组字段
    value_key: 分析字段
    
    使用场景：
    - 多标段报价 → 按标段分组分析
    - 多年数据 → 按年份分组
    - 多品类 → 按品类分组
    """
    groups = defaultdict(list)
    for item in items:
        groups[item[group_key]].append(item)
    
    all_results = []
    summary = []
    
    for group_name, group_items in groups.items():
        # 转换为统一格式
        prices = [{"投标人": g.get("投标人") or g.get("名称") or str(i),
                   "报价": g[value_key]} 
                  for i, g in enumerate(group_items)]
        
        results = stddev_outlier(prices, sigma)
        
        # 添加分组信息
        for i, r in enumerate(results):
            r[group_key] = group_name
            # 保留原始数据
            if "投标人" in group_items[i]:
                r["原始数据"] = {k: v for k, v in group_items[i].items() 
                               if k not in [group_key, value_key]}
        
        all_results.extend(results)
        
        outliers = [r for r in results if r["标志"]]
        if outliers:
            summary.append({
                "分组": group_name,
                "样本数": len(results),
                "异常数": len(outliers),
                "异常详情": [(r["投标人"], r["报价"], r["标志"]) for r in outliers]
            })
    
    return all_results, summary


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("STDDEV标准差异常检测 — 报价分析")
    print("=" * 60)
    
    # 示例1：单项目报价
    sample = [
        {"投标人":"A","报价":645},
        {"投标人":"B","报价":685},
        {"投标人":"C","报价":695},
        {"投标人":"D","报价":720},
        {"投标人":"E","报价":650},
        {"投标人":"F","报价":420},  # 异常低
        {"投标人":"G","报价":680},
        {"投标人":"H","报价":950},  # 异常高
        {"投标人":"I","报价":660},
        {"投标人":"J","报价":675},
    ]
    
    results = stddev_outlier(sample, sigma=2.0)
    
    print(f"\n样本数: {len(sample)}")
    for r in results:
        flag_display = f"  ⚠️ {r['标志']}" if r["标志"] else ""
        print(f"  {r['投标人']:4s} 报价={r['报价']:4d}  "
              f"Z={r['Z分数']:+5.1f}  百分位={r['百分位']:3.0f}%{flag_display}")
    
    # 示例2：分组分析
    print(f"\n{'='*60}")
    print("分组STDDEV — 多项目报价")
    print("=" * 60)
    
    multi = [
        {"项目":"P1","投标人":"A","报价":100}, {"项目":"P1","投标人":"B","报价":120},
        {"项目":"P1","投标人":"C","报价":110}, {"项目":"P1","投标人":"D","报价":300},
        {"项目":"P2","投标人":"E","报价":500}, {"项目":"P2","投标人":"F","报价":510},
        {"项目":"P2","投标人":"G","报价":505}, {"项目":"P2","投标人":"H","报价":800},
    ]
    
    _, summary = group_stddev(multi, "项目", "报价", sigma=1.5)
    
    for s in summary:
        print(f"\n  {s['分组']}: {s['样本数']}个样本, {s['异常数']}个异常")
        for name, val, flag in s["异常详情"]:
            print(f"    {name}: {val} ({flag})")
    
    print(f"\n阈值建议:")
    print(f"  σ=1.0: 宽松（约32%样本被标记）→ 初筛阶段")
    print(f"  σ=2.0: 适中（约5%样本被标记）→ 常规检测")
    print(f"  σ=3.0: 严格（约0.3%样本被标记）→ 确定性证据")

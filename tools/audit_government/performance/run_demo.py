"""
绩效评价场景 — 实战演练

模拟某市2025年度"乡村振兴专项资金"绩效评价，
涵盖6个区县同类项目的多源数据融合评分 + 横向对标。

作者：融策审计智析Agent | 日期：2026-07-22
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from economic_responsibility.all_tools import multi_source_scoring, performance_benchmark
from mcp_server import get_tools_by_tag, call_tool


# ═══════════════════════════════════════════════════════
# 场景设定
# ═══════════════════════════════════════════════════════

print("=" * 70)
print("  XX市2025年度乡村振兴专项资金 — 绩效评价审计报告")
print("=" * 70)
print(f"  审计期间: 2025-01-01 至 2025-12-31")
print(f"  专项资金总额: 2.4亿元")
print(f"  覆盖区县: 6个")
print(f"  评价方法: 多源数据融合 + 横向对标")
print()

# ═══════════════════════════════════════════════════════
# 一、多源数据融合绩效评分
# ═══════════════════════════════════════════════════════

print("-" * 60)
print("一、多源数据融合绩效评分（全市汇总）")
print("-" * 60)

# 四个数据源
fiscal_data = {
    "预算执行率": 92,
    "资金拨付及时率": 85,
    "配套资金到位率": 78,
    "资金使用合规率": 95,
}

business_data = {
    "项目完工率": 88,
    "建设质量达标率": 91,
    "惠及农户覆盖率": 76,
    "产业带动效果": 82,
    "基础设施改善度": 87,
}

third_party_data = {
    "第三方验收通过率": 90,
    "第三方满意度测评": 80,
}

satisfaction_data = {
    "农户满意度": 73,
    "村集体满意度": 79,
}

weights = {"fiscal": 0.25, "business": 0.30, "third_party": 0.15, "satisfaction": 0.30}

result = multi_source_scoring(fiscal_data, business_data, third_party_data, satisfaction_data, weights=weights)
d = result["data"]

print(f"\n  综合绩效评分: {d['total_score']}分 [{d['level']}]")
print(f"\n  分维度评分:")
for dim, scores in d["dimension_scores"].items():
    name = {"fiscal": "财政执行", "business": "业务产出", "third_party": "第三方评价", "satisfaction": "满意度"}[dim]
    bar = "█" * int(scores["avg_raw"] / 10) + "░" * (10 - int(scores["avg_raw"] / 10))
    print(f"    {name} (权重{scores['weight']}): {scores['avg_raw']}分 → 加权{scores['weighted_score']}分 {bar}")

print(f"\n  ⚠️ 短板分析:")
for dim, scores in d["dimension_scores"].items():
    name = {"fiscal": "财政执行", "business": "业务产出", "third_party": "第三方评价", "satisfaction": "满意度"}[dim]
    for ind, val in scores["indicators"].items():
        if val < 80:
            print(f"    [{name}] {ind}: {val}分 — 低于80分及格线")

# ═══════════════════════════════════════════════════════
# 二、6区县横向绩效对标
# ═══════════════════════════════════════════════════════

print("\n" + "-" * 60)
print("二、6区县横向绩效对标分析")
print("-" * 60)

projects = [
    {"name": "A区", "type": "乡村振兴", "budget": 5000, "output_qty": 12, "duration_days": 320, "quality_score": 94, "satisfaction": 85},
    {"name": "B区", "type": "乡村振兴", "budget": 4500, "output_qty": 10, "duration_days": 340, "quality_score": 89, "satisfaction": 80},
    {"name": "C区", "type": "乡村振兴", "budget": 4800, "output_qty": 14, "duration_days": 300, "quality_score": 96, "satisfaction": 88},
    {"name": "D区", "type": "乡村振兴", "budget": 3000, "output_qty": 6,  "duration_days": 380, "quality_score": 72, "satisfaction": 58},
    {"name": "E区", "type": "乡村振兴", "budget": 4200, "output_qty": 11, "duration_days": 350, "quality_score": 85, "satisfaction": 76},
    {"name": "F区", "type": "乡村振兴", "budget": 3500, "output_qty": 5,  "duration_days": 420, "quality_score": 68, "satisfaction": 52},
]

result2 = performance_benchmark(projects)
d2 = result2["data"]

print(f"\n  共{d2['benchmarks'] and len(d2['benchmarks'])}个区县参与对标")
print(f"  标杆项目: {d2['best_project']}")
print(f"  最差项目: {d2['worst_project']}")

print(f"\n  各维偏离度一览:")
header = f"  {'区县':<6} {'预算':>6} {'产出':>5} {'工期':>5} {'质量':>5} {'满意':>5} {'总偏离':>6} {'判定':>6}"
print(header)
print("  " + "-" * 50)

for b in d2["benchmarks"]:
    devs = b["deviations"]
    total = b["total_deviation"]
    flag = "⚠️异常" if b["flag"] == "outlier" else "正常"
    print(f"  {b['name']:<6} {b['budget']:>6} {devs.get('output_qty',0):>+5.1f} {devs.get('duration_days',0):>+5.1f} {devs.get('quality_score',0):>+5.1f} {devs.get('satisfaction',0):>+5.1f} {total:>6.2f} {flag:>6}")

print(f"\n  🔴 异常项目 ({len(d2['outliers'])}个):")
for name in d2["outliers"]:
    print(f"    - {name}")

# ═══════════════════════════════════════════════════════
# 三、综合审计结论
# ═══════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("  综合审计结论")
print("=" * 70)

issues = []
recommendations = []

# 来自多源评分
for dim, scores in d["dimension_scores"].items():
    name = {"fiscal": "财政执行", "business": "业务产出", "third_party": "第三方评价", "satisfaction": "满意度"}[dim]
    for ind, val in scores["indicators"].items():
        if val < 80:
            issues.append(f"【{name}】{ind}: {val}分（低于80分及格线）")

# 来自横向对标
for name in d2["outliers"]:
    proj = next((p for p in projects if p["name"] == name), None)
    if proj:
        if proj["quality_score"] < 75:
            issues.append(f"【{name}】建设质量{proj['quality_score']}分，严重低于全市平均水平，建议专项核查")
        if proj["satisfaction"] < 60:
            issues.append(f"【{name}】农户满意度{proj['satisfaction']}分，存在民生诉求未满足风险")
        if proj["duration_days"] > 400:
            issues.append(f"【{name}】工期{proj['duration_days']}天，严重超期，需核实是否存在管理缺陷")

# 标杆经验
best = next((p for p in projects if p["name"] == d2.get("best_project")), None)
if best:
    recommendations.append(f"推广{best['name']}经验：产出{best['output_qty']}项、质量{best['quality_score']}分、满意度{best['satisfaction']}分，均为全市最优")

# 针对短板
low_satisfaction = [p["name"] for p in projects if p["satisfaction"] < 70]
if low_satisfaction:
    recommendations.append(f"满意度提升：{', '.join(low_satisfaction)}农户满意度低于70分，建议开展入户回访，梳理诉求清单")

if any(p["duration_days"] > 365 for p in projects):
    recommendations.append("工期管控：超期项目建议建立红黄绿灯预警机制，按月通报建设进度")

recommendations.append("资金监管：配套资金到位率仅78%，建议建立县级配套资金承诺+督查机制")
recommendations.append("结果应用：将绩效评价结果纳入下一年度资金分配的权重不低于30%")

print(f"\n  发现问题 {len(issues)} 项:")
for i, iss in enumerate(issues, 1):
    print(f"    {i}. {iss}")

print(f"\n  整改建议 {len(recommendations)} 条:")
for i, rec in enumerate(recommendations, 1):
    print(f"    {i}. {rec}")

# 绩效等级
overall_score = d["total_score"]
outlier_count = len(d2["outliers"])
if overall_score >= 85 and outlier_count == 0:
    final_grade = "优"
elif overall_score >= 75 and outlier_count <= 1:
    final_grade = "良"
elif overall_score >= 60:
    final_grade = "中"
else:
    final_grade = "差"

print(f"\n  绩效评价等级: {final_grade}")
print(f"  （综合评分{overall_score}分，异常区县{outlier_count}个）")

print("\n" + "=" * 70)
print("  审计工具调用链")
print("=" * 70)
tools_used = get_tools_by_tag("绩效评价")
print(f"  本场景涉及工具: {len(tools_used)}个")
for t in tools_used:
    print(f"    - {t['name']}: {t['description'][:60]}...")

print(f"\n✅ 绩效评价场景审计完成")

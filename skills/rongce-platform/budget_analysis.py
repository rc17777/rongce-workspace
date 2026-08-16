"""
预算执行分析模型 (Budget Execution Analysis Model)
=================================================
对预算编制、执行进度、偏差情况进行多维度分析。
支持：执行率分析、年底突击花钱检测、预算异常波动、趋势分析。

使用方式：
  py budget_analysis.py --file 预算执行数据.csv --output 分析结果.json
  py budget_analysis.py --sample                   # 示例数据

数据输入格式（CSV）：
  item_code, item_name, budget_amount, actual_amount, q1_actual, q2_actual, q3_actual, q4_actual, department, year
"""

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import csv
import json
import sys
import math as _math
from datetime import datetime
from collections import Counter


def budget_analysis(data, year=None):
    """
    预算执行分析主函数

    输入: data = [{
        'item_code': 'B001',
        'item_name': '办公费',
        'budget_amount': 100000,
        'actual_amount': 85000,
        'q1_actual': 20000,
        'q2_actual': 25000,
        'q3_actual': 22000,
        'q4_actual': 18000,
        'department': '办公室',
        'year': 2025
    }, ...]

    输出: {
        'items': [...], 每项的分析结果
        'summary': {...}, 总体统计
        'flagged': [...] 需关注事项
    }
    """
    if year:
        data = [d for d in data if str(d.get('year', '')) == str(year)]

    if not data:
        return {"items": [], "summary": {}, "flagged": []}

    results = []
    flagged = []
    total_budget = 0
    total_actual = 0
    year_end_count = 0

    for item in data:
        budget = float(item.get("budget_amount", 0) or 0)
        actual = float(item.get("actual_amount", 0) or 0)
        q1 = float(item.get("q1_actual", 0) or 0)
        q2 = float(item.get("q2_actual", 0) or 0)
        q3 = float(item.get("q3_actual", 0) or 0)
        q4 = float(item.get("q4_actual", 0) or 0)

        # 执行率
        execution_rate = actual / budget if budget > 0 else 0

        # 偏差分析
        deviation_type = None
        risk_level = "正常"
        risk_score = 0

        if execution_rate < 0.5 and budget > 0:
            deviation_type = "执行严重不足"
            risk_level = "高"
            risk_score = 15
        elif execution_rate > 1.2 and budget > 0:
            deviation_type = "超预算执行"
            risk_level = "高"
            risk_score = 20
        elif execution_rate > 1.0 and budget > 0:
            deviation_type = "预算不足"
            risk_level = "中"
            risk_score = 10
        elif execution_rate == 0 and budget > 0:
            deviation_type = "完全未执行"
            risk_level = "高"
            risk_score = 25

        # 年底突击花钱检测（Q4占比>50% 或 Q4>Q1*3）
        year_end_spike = False
        total_q = q1 + q2 + q3 + q4
        if total_q > 0:
            q4_ratio = q4 / total_q
            if q4_ratio > 0.5:
                year_end_spike = True
                risk_level = "高"
                risk_score += 25
                deviation_type = "年底突击花钱" if not deviation_type else deviation_type + "+年底突击"

            # Q4远超Q1的检测
            if q1 > 0 and q4 > q1 * 3:
                year_end_spike = True
                risk_score += 15

        # 季度波动检测（标准差分析）
        quarters = [q1, q2, q3, q4]
        mean_q = sum(quarters) / 4
        if mean_q > 0:
            q_variance = sum((q - mean_q) ** 2 for q in quarters) / 4
            cv = _math.sqrt(q_variance) / mean_q  # 变异系数
            if cv > 0.8:
                risk_level = "高" if risk_level != "高" else risk_level
                risk_score += 10

                if not deviation_type:
                    deviation_type = "季度波动异常"
                if "波动" not in deviation_type:
                    deviation_type += "+季度波动异常"

        # 构建结果
        item_result = {
            "item_code": item.get("item_code", ""),
            "item_name": item.get("item_name", ""),
            "department": item.get("department", ""),
            "budget": budget,
            "actual": actual,
            "execution_rate": round(execution_rate * 100, 2),
            "q1": q1, "q2": q2, "q3": q3, "q4": q4,
            "deviation_type": deviation_type or "正常",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "year_end_spike": year_end_spike,
        }
        results.append(item_result)
        total_budget += budget
        total_actual += actual
        if year_end_spike:
            year_end_count += 1

        # 收集需关注项
        if risk_level in ("高", "极高"):
            flagged.append({
                "type": deviation_type or "异常",
                "item": item_result["item_name"],
                "detail": f"执行率{item_result['execution_rate']}%，预算{budget:.0f}，实际{actual:.0f}",
            })

    # 总体统计
    overall_rate = round(total_actual / total_budget * 100, 2) if total_budget > 0 else 0
    summary = {
        "total_items": len(data),
        "total_budget": total_budget,
        "total_actual": total_actual,
        "overall_execution_rate": overall_rate,
        "high_risk_count": len([r for r in results if r["risk_level"] == "高"]),
        "medium_risk_count": len([r for r in results if r["risk_level"] == "中"]),
        "year_end_spike_count": year_end_count,
        "flagged_count": len(flagged),
    }

    return {"items": results, "summary": summary, "flagged": flagged}


def print_report(result):
    """打印分析报告"""
    s = result["summary"]
    print("=" * 60)
    print(f"  预算执行分析报告")
    print(f"  分析项数: {s['total_items']}")
    print(f"  总预算: {s['total_budget']:,.2f}")
    print(f"  总执行: {s['total_actual']:,.2f}")
    print(f"  整体执行率: {s['overall_execution_rate']}%")
    print("=" * 60)
    print(f"  🔴 高风险项: {s['high_risk_count']}")
    print(f"  🟡 中风险项: {s['medium_risk_count']}")
    print(f"  ⚠️  年底突击花钱疑似: {s['year_end_spike_count']}")
    print(f"  📋 需关注事项: {s['flagged_count']}")
    print("=" * 60)

    # 高风险明细
    high_items = [r for r in result["items"] if r["risk_level"] == "高"]
    if high_items:
        print(f"\n⚠️  高风险项:")
        for r in sorted(high_items, key=lambda x: -x["risk_score"]):
            icon = "🎯" if r["year_end_spike"] else "📌"
            rate_str = f"{r['execution_rate']:>6.2f}%"
            print(f"  {icon} {r['item_name']:15s} | {r['department']:8s} | 预算:{r['budget']:>10,.0f} | 执行:{r['actual']:>10,.0f} | 执行率:{rate_str} | {r['deviation_type']}")

    # 正常项统计
    normal_count = len([r for r in result["items"] if r["risk_level"] == "正常"])
    print(f"\n  ✅ 正常项: {normal_count}")
    print(f"  ➡️  整体执行率: {s['overall_execution_rate']}%")

    if result["flagged"]:
        print(f"\n📋 需关注事项:")
        for i, f in enumerate(result["flagged"], 1):
            print(f"  {i}. [{f['type']}] {f['item']} — {f['detail']}")


def load_csv(filepath):
    """从CSV加载数据"""
    data = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ["budget_amount", "actual_amount", "q1_actual", "q2_actual", "q3_actual", "q4_actual"]:
                try:
                    row[key] = float(row.get(key, 0) or 0)
                except (ValueError, TypeError):
                    row[key] = 0
            data.append(row)
    return data


# ========== 示例数据 ==========

SAMPLE_DATA = [
    {"item_code": "B001", "item_name": "办公费", "budget_amount": 100000, "actual_amount": 85000,
     "q1_actual": 20000, "q2_actual": 25000, "q3_actual": 22000, "q4_actual": 18000, "department": "办公室", "year": 2025},
    {"item_code": "B002", "item_name": "差旅费", "budget_amount": 80000, "actual_amount": 95000,
     "q1_actual": 15000, "q2_actual": 25000, "q3_actual": 30000, "q4_actual": 25000, "department": "业务部", "year": 2025},
    {"item_code": "B003", "item_name": "会议费", "budget_amount": 50000, "actual_amount": 15000,
     "q1_actual": 2000, "q2_actual": 3000, "q3_actual": 5000, "q4_actual": 5000, "department": "办公室", "year": 2025},
    {"item_code": "B004", "item_name": "设备采购", "budget_amount": 200000, "actual_amount": 180000,
     "q1_actual": 10000, "q2_actual": 20000, "q3_actual": 50000, "q4_actual": 100000, "department": "技术部", "year": 2025},
    {"item_code": "B005", "item_name": "培训费", "budget_amount": 30000, "actual_amount": 30000,
     "q1_actual": 5000, "q2_actual": 8000, "q3_actual": 10000, "q4_actual": 7000, "department": "人事部", "year": 2025},
    {"item_code": "B006", "item_name": "项目经费A", "budget_amount": 500000, "actual_amount": 0,
     "q1_actual": 0, "q2_actual": 0, "q3_actual": 0, "q4_actual": 0, "department": "项目部", "year": 2025},
    {"item_code": "B007", "item_name": "维修费", "budget_amount": 60000, "actual_amount": 78000,
     "q1_actual": 5000, "q2_actual": 8000, "q3_actual": 15000, "q4_actual": 50000, "department": "后勤部", "year": 2025},
    {"item_code": "B008", "item_name": "宣传费", "budget_amount": 40000, "actual_amount": 42000,
     "q1_actual": 3000, "q2_actual": 5000, "q3_actual": 14000, "q4_actual": 20000, "department": "宣传部", "year": 2025},
    {"item_code": "B009", "item_name": "信息化建设", "budget_amount": 300000, "actual_amount": 285000,
     "q1_actual": 20000, "q2_actual": 50000, "q3_actual": 100000, "q4_actual": 115000, "department": "技术部", "year": 2025},
    {"item_code": "B010", "item_name": "劳务费", "budget_amount": 120000, "actual_amount": 144000,
     "q1_actual": 25000, "q2_actual": 30000, "q3_actual": 39000, "q4_actual": 50000, "department": "业务部", "year": 2025},
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="预算执行分析模型")
    parser.add_argument("--file", help="预算执行数据CSV")
    parser.add_argument("--output", help="输出文件(.json)")
    parser.add_argument("--sample", action="store_true", help="示例数据")
    parser.add_argument("--year", type=int, default=2025, help="分析年份")
    args = parser.parse_args()

    if args.sample:
        data = SAMPLE_DATA
        print(f"使用内置示例数据（{len(data)}项，{args.year}年）")
    elif args.file:
        data = load_csv(args.file)
        print(f"加载CSV: {args.file}, {len(data)}条记录")
    else:
        data = SAMPLE_DATA
        print(f"未指定输入文件，使用内置示例数据")

    result = budget_analysis(data, year=args.year)
    print_report(result)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n结果已保存至: {args.output}")

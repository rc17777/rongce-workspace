"""
费用舞弊风险模型 (Expense Fraud Risk Model)
==========================================
基于8条风控规则 + 综合评分机制，对费用报销单/凭证进行财务舞弊风险评分。
支持单笔评分和批量评分，输出风险等级和每笔明细。

使用方式：
  py expense_fraud_model.py --file 凭证数据.csv --output 风险评分结果.xlsx
  py expense_fraud_model.py --sample            # 运行内置示例数据

数据输入格式（CSV）：
  voucher_id, amount, payee, payer, voucher_date, invoice_numbers, category, department
"""

import csv
import json
import os
import sys
import math
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import Counter

# ========== 规则配置 ==========

RULES = [
    {
        "id": "F001", "name": "大额整数报销",
        "condition": lambda r: r["amount"] >= 10000 and r["amount"] % 1000 == 0,
        "weight": 10, "level": "中",
        "desc": "金额≥10000且整千"
    },
    {
        "id": "F002", "name": "连号发票异常",
        "condition": lambda r: r.get("consecutive_invoice_count", 0) >= 5,
        "weight": 20, "level": "高",
        "desc": "同一单位连号发票≥5张"
    },
    {
        "id": "F003", "name": "高频小额报销",
        "condition": lambda r: r.get("monthly_count", 0) >= 20,
        "weight": 10, "level": "中",
        "desc": "同一人月报销次数≥20次"
    },
    {
        "id": "F004", "name": "节假日报销",
        "condition": lambda r: _is_holiday(r.get("voucher_date")),
        "weight": 20, "level": "高",
        "desc": "发票日期为法定节假日"
    },
    {
        "id": "F005", "name": "超标准报销",
        "condition": lambda r: r["amount"] > r.get("standard_limit", 999999),
        "weight": 20, "level": "高",
        "desc": "住宿/交通/餐费超标准"
    },
    {
        "id": "F006", "name": "关联方报销",
        "condition": lambda r: r.get("is_related_party", False),
        "weight": 40, "level": "极高",
        "desc": "收款方为关联企业/个人"
    },
    {
        "id": "F007", "name": "异常时间报销",
        "condition": lambda r: r.get("is_night_hours", False),
        "weight": 10, "level": "中",
        "desc": "凌晨/深夜时段报销"
    },
    {
        "id": "F008", "name": "重复报销",
        "condition": lambda r: r.get("is_duplicate", False),
        "weight": 40, "level": "极高",
        "desc": "同一发票多次报销"
    },
]

# 法定节假日（简版，按2025年设定）
HOLIDAYS_2025 = {
    date(2025, 1, 1), date(2025, 1, 28), date(2025, 1, 29), date(2025, 1, 30), date(2025, 1, 31),
    date(2025, 2, 1), date(2025, 2, 2), date(2025, 2, 3), date(2025, 2, 4),
    date(2025, 4, 4), date(2025, 4, 5), date(2025, 4, 6),
    date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 3), date(2025, 5, 4), date(2025, 5, 5),
    date(2025, 5, 31), date(2025, 6, 1), date(2025, 6, 2),
    date(2025, 10, 1), date(2025, 10, 2), date(2025, 10, 3), date(2025, 10, 4), date(2025, 10, 5),
    date(2025, 10, 6), date(2025, 10, 7), date(2025, 10, 8),
}

# 深夜时段：22:00-06:00
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6


def _is_holiday(date_val):
    """判断是否为法定节假日"""
    if date_val is None:
        return False
    try:
        if isinstance(date_val, str):
            d = datetime.strptime(date_val[:10], "%Y-%m-%d").date()
        else:
            d = date_val
        return d in HOLIDAYS_2025 or d.weekday() >= 5
    except (ValueError, TypeError):
        return False


def _is_night_hours(datetime_str):
    """判断是否为深夜时段"""
    if not datetime_str:
        return False
    try:
        h = int(str(datetime_str)[11:13])
        return h >= NIGHT_START_HOUR or h < NIGHT_END_HOUR
    except (ValueError, IndexError, TypeError):
        return False


def _parse_date(val):
    """安全的日期解析"""
    if val is None:
        return None
    try:
        s = str(val).strip()
        if len(s) >= 10:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        return None
    except ValueError:
        return None


# ========== 核心评分函数 ==========

def score_single_voucher(voucher):
    """
    对单张凭证进行综合风险评分

    输入: voucher dict，字段见下方说明
    输出: {'score': int, 'level': str, 'triggered_rules': [rule_ids], 'details': str}
    """
    # 添加派生字段
    voucher["is_night_hours"] = _is_night_hours(voucher.get("voucher_date", ""))
    voucher["voucher_date_parsed"] = _parse_date(voucher.get("voucher_date"))

    total_score = 0
    triggered = []

    for rule in RULES:
        try:
            if rule["condition"](voucher):
                total_score += rule["weight"]
                triggered.append(rule["id"])
        except Exception:
            continue

    # 打等级
    if total_score >= 60:
        level = "极高风险"
    elif total_score >= 40:
        level = "高风险"
    elif total_score >= 20:
        level = "中风险"
    else:
        level = "低风险"

    return {
        "score": total_score,
        "level": level,
        "triggered_rules": triggered,
        "triggered_names": [r["name"] for r in RULES if r["id"] in triggered],
        "severity": "🔴" if total_score >= 60 else ("🟡" if total_score >= 40 else ("🔵" if total_score >= 20 else "🟢"))
    }


def batch_score(vouchers, with_pre_analysis=False):
    """
    批量评分 + 可选前置分析（高频/连号检测）

    输入: vouchers 为 dict 列表
    输出: dict {results: [...], summary: {...}}
    """
    # 前置分析：统计频次和连号
    if with_pre_analysis:
        # 按报销人统计月度频次
        monthly_counts = Counter()
        for v in vouchers:
            key = f"{v.get('payer','?')}|{str(v.get('voucher_date',''))[:7]}"
            monthly_counts[key] += 1

        # 添加前置分析字段
        for v in vouchers:
            payer_key = f"{v.get('payer','?')}|{str(v.get('voucher_date',''))[:7]}"
            v["monthly_count"] = monthly_counts.get(payer_key, 0)
            # 模拟连号检测（同一人同一天的发票若有规律编号）
            v["consecutive_invoice_count"] = v.get("consecutive_invoice_count", 0)
            v["is_duplicate"] = v.get("is_duplicate", False)
            v["is_related_party"] = v.get("is_related_party", False)

    # 评分
    results = []
    for v in vouchers:
        result = score_single_voucher(v)
        result["voucher_id"] = v.get("voucher_id", "?")
        result["amount"] = v.get("amount", 0)
        result["payer"] = v.get("payer", "?")
        result["payee"] = v.get("payee", "?")
        result["voucher_date"] = v.get("voucher_date", "?")
        results.append(result)

    # 汇总
    high_risk = [r for r in results if r["level"] in ("高风险", "极高风险")]
    summary = {
        "total": len(results),
        "极高风险": len([r for r in results if r["level"] == "极高风险"]),
        "高风险": len([r for r in results if r["level"] == "高风险"]),
        "中风险": len([r for r in results if r["level"] == "中风险"]),
        "低风险": len([r for r in results if r["level"] == "低风险"]),
        "涉及金额_高风险": sum(r["amount"] for r in high_risk),
        "最高分": max((r["score"] for r in results), default=0),
        "平均分": sum(r["score"] for r in results) / len(results) if results else 0,
    }

    return {"results": results, "summary": summary}


def load_csv(filepath):
    """从CSV加载凭证数据"""
    vouchers = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["amount"] = float(row.get("amount", 0))
            except (ValueError, TypeError):
                row["amount"] = 0
            vouchers.append(row)
    return vouchers


def print_report(result):
    """打印评分结果报告"""
    s = result["summary"]
    print("=" * 60)
    print(f"  费用舞弊风险评分报告")
    print(f"  评估凭证数: {s['total']}")
    print(f"  最高风险分: {s['最高分']}")
    print(f"  平均风险分: {s['平均分']:.1f}")
    print("=" * 60)
    print(f"  🔴 极高风险: {s['极高风险']} 笔")
    print(f"  🟡 高风险:   {s['高风险']} 笔")
    print(f"  🔵 中风险:   {s['中风险']} 笔")
    print(f"  🟢 低风险:   {s['低风险']} 笔")
    print(f"  高风险涉及总金额: {s['涉及金额_高风险']:.2f}")
    print("=" * 60)

    # 高风险详情
    high = [r for r in result["results"] if r["level"] in ("高风险", "极高风险")]
    if high:
        print("\n⚠️  高风险凭证明细:")
        print(f"  {'凭证ID':12s} {'金额':>12s} {'报销人':8s} {'评分':>5s} {'等级':8s} {'触发规则'}")
        print("  " + "-" * 65)
        for r in sorted(high, key=lambda x: -x["score"]):
            rules = ",".join(r["triggered_names"][:3])
            if len(r["triggered_names"]) > 3:
                rules += f"...({len(r['triggered_names'])}条)"
            print(f"  {r['voucher_id']:12s} {r['amount']:>12.2f} {r['payer']:8s} {r['score']:>5d} {r['level']:8s} {rules}")


# ========== 示例数据 ==========

SAMPLE_DATA = [
    {"voucher_id": "V001", "amount": 10000, "payee": "XX科技公司", "payer": "张三",
     "voucher_date": "2025-03-15 10:30", "invoice_numbers": "INV2025001", "category": "办公设备"},
    {"voucher_id": "V002", "amount": 99999, "payee": "YY咨询公司", "payer": "李四",
     "voucher_date": "2025-01-01 09:00", "invoice_numbers": "INV2025002-INV2025006",
     "consecutive_invoice_count": 5, "category": "咨询服务"},
    {"voucher_id": "V003", "amount": 5000, "payee": "ZZ酒店", "payer": "张三",
     "voucher_date": "2025-01-01 23:30", "invoice_numbers": "INV2025007", "category": "住宿",
     "is_night_hours": True},
    {"voucher_id": "V004", "amount": 80000, "payee": "关联企业A", "payer": "王五",
     "voucher_date": "2025-06-15 14:00", "invoice_numbers": "INV2025008",
     "is_related_party": True, "category": "采购"},
    {"voucher_id": "V005", "amount": 12500, "payee": "文具店", "payer": "张三",
     "voucher_date": "2025-02-28 16:00", "invoice_numbers": "INV2025009",
     "monthly_count": 22, "category": "办公用品"},
    {"voucher_id": "V006", "amount": 3500, "payee": "XX科技公司", "payer": "赵六",
     "voucher_date": "2025-03-10 11:00", "invoice_numbers": "INV2025010", "category": "软件服务"},
    {"voucher_id": "V007", "amount": 150000, "payee": "YY咨询公司", "payer": "钱七",
     "voucher_date": "2025-04-05 10:00", "invoice_numbers": "INV2025011-INV2025015",
     "consecutive_invoice_count": 5, "is_related_party": True, "category": "咨询费"},
    {"voucher_id": "V008", "amount": 5000, "payee": "ZZ商贸", "payer": "孙八",
     "voucher_date": "2025-05-02 02:15", "invoice_numbers": "INV2025016",
     "is_night_hours": True, "category": "办公耗材"},
    {"voucher_id": "V009", "amount": 88888, "payee": "XX科技公司", "payer": "周九",
     "voucher_date": "2025-09-15 15:30", "invoice_numbers": "INV2025017-INV2025018",
     "is_related_party": True, "is_night_hours": True, "category": "技术服务"},
    {"voucher_id": "V010", "amount": 60000, "payee": "快印店", "payer": "王五",
     "voucher_date": "2025-07-01 10:00", "invoice_numbers": "INV2025019",
     "is_duplicate": True, "category": "印刷"},
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="费用舞弊风险模型")
    parser.add_argument("--file", help="凭证数据CSV文件路径")
    parser.add_argument("--output", help="输出结果文件(.json/.xlsx)")
    parser.add_argument("--sample", action="store_true", help="使用内置示例数据")
    args = parser.parse_args()

    data = None
    if args.sample:
        data = SAMPLE_DATA
        print("使用内置示例数据")
    elif args.file:
        data = load_csv(args.file)
        print(f"加载CSV: {args.file}, {len(data)}条记录")
    else:
        data = SAMPLE_DATA
        print("未指定输入文件，使用内置示例数据")

    result = batch_score(data, with_pre_analysis=True)
    print_report(result)

    if args.output:
        ext = os.path.splitext(args.output)[1].lower()
        if ext == ".json":
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"结果已保存至: {args.output}")
        else:
            print(f"支持 .json 格式输出，不支持的格式: {ext}")

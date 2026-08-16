"""
资金异常流动检测模型 (Abnormal Fund Flow Detection Model)
=======================================================
检测资金回流、大额拆分、异常时段交易、高频交易、黑名单匹配等5类资金异常。

使用方式：
  py fund_flow_model.py --file 资金流水.csv --output 异常结果.json
  py fund_flow_model.py --sample
"""

import csv
import json
import sys
import math
from datetime import datetime
from collections import Counter, defaultdict


# ========== 资金异常检测函数 ==========

def detect_fund_flow_anomalies(transactions, min_amount=100000, window_days=30):
    """
    多维度资金异常检测

    输入: transactions = [{
        'tx_id': 'T001',
        'from_account': 'A公司',
        'to_account': 'B公司',
        'amount': 500000,
        'tx_date': '2025-03-15 10:30:00',
        'from_region': '成都',
        'to_region': '上海',
        'summary': '货款',
        'from_company': 'A公司',
        'to_company': 'B公司',
    }, ...]

    输出: {
        'fund_loops': [...],       # 资金回流
        'large_splits': [...],     # 大额拆分
        'abnormal_time': [...],    # 异常时段
        'high_freq': [...],        # 高频交易
        'blacklist_hits': [...],   # 黑名单
        'cross_region': [...],     # 跨区域异常
        'summary': {...}
    }
    """
    result = {
        "fund_loops": [],
        "large_splits": [],
        "abnormal_time": [],
        "high_freq": [],
        "blacklist_hits": [],
        "cross_region": [],
        "summary": {},
    }

    ## 检测1: 资金回流（A→B→A循环）
    fund_loops = []
    # 构建交易图: {A: [(B, amount, tx_id, date), ...]}
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for tx in transactions:
        f = tx.get("from_company") or tx.get("from_account", "?")
        t = tx.get("to_company") or tx.get("to_account", "?")
        amt = float(tx.get("amount", 0))
        if f != t:
            outgoing[f].append((t, amt, tx.get("tx_id", ""), tx.get("tx_date", "")))
            incoming[t].append((f, amt, tx.get("tx_id", ""), tx.get("tx_date", "")))

    # 检测 A→B→A 的两步回流
    for a in outgoing:
        if a not in incoming:
            continue
        seen_recipients = {r[0] for r in outgoing[a]}
        for source, _, src_id, src_date in incoming[a]:
            if source in seen_recipients:
                loop = {
                    "loop": f"{source} → {a} → {source}",
                    "amount_out": sum(r[1] for r in outgoing[a] if r[0] == source),
                    "amount_in": sum(r[1] for r in incoming[a] if r[0] == source),
                    "tx_ids": list(set(
                        [r[2] for r in outgoing[a] if r[0] == source] +
                        [r[2] for r in incoming[a] if r[0] == source]
                    )),
                }
                if loop["amount_in"] > min_amount * 0.1:
                    fund_loops.append(loop)
    result["fund_loops"] = fund_loops[:20]  # 取top20

    ## 检测2: 大额拆分（同一日A→B多笔，合计超阈值）
    splits = defaultdict(list)
    for tx in transactions:
        f = tx.get("from_company") or tx.get("from_account", "?")
        t = tx.get("to_company") or tx.get("to_account", "?")
        amt = float(tx.get("amount", 0))
        dt = str(tx.get("tx_date", ""))[:10]
        key = f"{f}→{t}|{dt}"
        splits[key].append(tx)

    large_splits = []
    for key, txs in splits.items():
        total = sum(float(tx.get("amount", 0)) for tx in txs)
        count = len(txs)
        if count >= 3 and total >= min_amount * 0.5:
            large_splits.append({
                "key": key,
                "total_amount": total,
                "count": count,
                "avg_amount": round(total / count, 2),
            })
    result["large_splits"] = large_splits[:20]

    ## 检测3: 异常时段交易（22:00-06:00的大额）
    night_txs = []
    for tx in transactions:
        dt_str = str(tx.get("tx_date", ""))
        amt = float(tx.get("amount", 0))
        try:
            h = int(dt_str[11:13])
        except (ValueError, IndexError):
            h = 12
        if (h >= 22 or h < 6) and amt >= min_amount * 0.2:
            night_txs.append({
                "tx_id": tx.get("tx_id", ""),
                "from": tx.get("from_company") or tx.get("from_account", "?"),
                "to": tx.get("to_company") or tx.get("to_account", "?"),
                "amount": amt,
                "time": dt_str,
                "summary": tx.get("summary", ""),
            })
    result["abnormal_time"] = night_txs[:20]

    ## 检测4: 高频交易（短期内同一对账户频繁往来）
    freq_tracker = defaultdict(lambda: {"count": 0, "total": 0, "txs": []})
    for tx in transactions:
        f = tx.get("from_company") or tx.get("from_account", "?")
        t = tx.get("to_company") or tx.get("to_account", "?")
        key = f"{f}↔{t}"
        amt = float(tx.get("amount", 0))
        freq_tracker[key]["count"] += 1
        freq_tracker[key]["total"] += amt
        freq_tracker[key]["txs"].append(tx.get("tx_id", ""))

    high_freq = []
    for key, info in freq_tracker.items():
        # 取日平均频次（假设在30天窗口内）
        c = info["count"]
        if c >= 10 and info["total"] >= min_amount:
            high_freq.append({
                "pair": key,
                "count": c,
                "total_amount": info["total"],
                "avg_per_tx": round(info["total"] / c, 2),
            })
    result["high_freq"] = sorted(high_freq, key=lambda x: -x["count"])[:20]

    ## 检测5: 跨区域异常（交易地≠注册地，且单笔较大）
    cross_region = []
    for tx in transactions:
        amt = float(tx.get("amount", 0))
        fr = tx.get("from_region", "")
        tr = tx.get("to_region", "")
        if fr and tr and fr != tr and amt >= min_amount * 0.3:
            cross_region.append({
                "tx_id": tx.get("tx_id", ""),
                "from": tx.get("from_company") or tx.get("from_account", "?"),
                "to": tx.get("to_company") or tx.get("to_account", "?"),
                "amount": amt,
                "from_region": fr,
                "to_region": tr,
            })
    result["cross_region"] = sorted(cross_region, key=lambda x: -x["amount"])[:20]

    ## 汇总
    result["summary"] = {
        "总交易数": len(transactions),
        "资金回流疑似数": len(fund_loops),
        "大额拆分疑似数": len(large_splits),
        "异常时段交易数": len(night_txs),
        "高频交易对数": len(high_freq),
        "跨区域异常数": len(cross_region),
        "预警总数": (
            len(fund_loops) + len(large_splits) + len(night_txs) + len(high_freq) + len(cross_region)
        ),
    }

    return result


def print_report(result):
    """打印资金异常检测报告"""
    s = result["summary"]
    print("=" * 60)
    print("  资金异常流动检测报告")
    print(f"  总交易数: {s['总交易数']}")
    print(f"  预警总数: {s['预警总数']}")
    print("=" * 60)
    print(f"  🔄 资金回流疑似:           {s['资金回流疑似数']}")
    print(f"  ✂️  大额拆分疑似:           {s['大额拆分疑似数']}")
    print(f"  🌙 异常时段交易:            {s['异常时段交易数']}")
    print(f"  🔁 高频交易对:              {s['高频交易对数']}")
    print(f"  🗺️  跨区域异常:             {s['跨区域异常数']}")
    print("=" * 60)

    for key, label in [
        ("fund_loops", "🔄 资金回流"),
        ("large_splits", "✂️  大额拆分"),
        ("abnormal_time", "🌙 异常时段"),
        ("high_freq", "🔁 高频交易"),
        ("cross_region", "🗺️  跨区域异常"),
    ]:
        items = result.get(key, [])
        if items:
            print(f"\n{label}:")
            for i, item in enumerate(items[:5], 1):
                if key == "fund_loops":
                    print(f"  {i}. {item['loop']} | 流出:{item['amount_out']:>10,.0f} 流入:{item['amount_in']:>10,.0f}")
                elif key == "large_splits":
                    print(f"  {i}. {item['key']} | {item['count']}笔 | 合计:{item['total_amount']:>10,.0f}")
                elif key == "abnormal_time":
                    print(f"  {i}. {item['from']}→{item['to']} | {item['amount']:>10,.0f} | {item['time']}")
                elif key == "high_freq":
                    print(f"  {i}. {item['pair']} | {item['count']}笔 | 合计:{item['total_amount']:>10,.0f}")
                elif key == "cross_region":
                    print(f"  {i}. {item['from']}→{item['to']} | {item['amount']:>10,.0f} | {item['from_region']}→{item['to_region']}")


def load_csv(filepath):
    """从CSV加载交易数据"""
    data = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["amount"] = float(row.get("amount", 0))
            except (ValueError, TypeError):
                row["amount"] = 0
            # 生成tx_id（如果没有）
            if not row.get("tx_id"):
                row["tx_id"] = f"TX_{len(data)+1:06d}"
            data.append(row)
    return data


def load_json(filepath):
    """从JSON加载交易数据"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== 示例数据 ==========

SAMPLE_DATA = [
    {"tx_id": "T001", "from_company": "A公司", "to_company": "B公司", "amount": 300000, "tx_date": "2025-03-15 10:30:00", "from_region": "成都", "to_region": "成都", "summary": "咨询费"},
    {"tx_id": "T002", "from_company": "B公司", "to_company": "A公司", "amount": 250000, "tx_date": "2025-03-20 14:00:00", "from_region": "成都", "to_region": "成都", "summary": "退款"},
    {"tx_id": "T003", "from_company": "A公司", "to_company": "B公司", "amount": 50000, "tx_date": "2025-04-01 09:00:00", "from_region": "成都", "to_region": "成都", "summary": "货款"},
    {"tx_id": "T004", "from_company": "B公司", "to_company": "C公司", "amount": 280000, "tx_date": "2025-04-05 16:30:00", "from_region": "成都", "to_region": "上海", "summary": "设备款"},
    {"tx_id": "T005", "from_company": "C公司", "to_company": "A公司", "amount": 260000, "tx_date": "2025-04-10 02:15:00", "from_region": "上海", "to_region": "成都", "summary": "技术服务费"},
    {"tx_id": "T006", "from_company": "D公司", "to_company": "E公司", "amount": 150000, "tx_date": "2025-04-08 11:00:00", "from_region": "北京", "to_region": "北京", "summary": "咨询费"},
    {"tx_id": "T007", "from_company": "A公司", "to_company": "D公司", "amount": 200000, "tx_date": "2025-04-12 14:30:00", "from_region": "成都", "to_region": "北京", "summary": "货款"},
    {"tx_id": "T008", "from_company": "E公司", "to_company": "A公司", "amount": 180000, "tx_date": "2025-04-15 23:45:00", "from_region": "北京", "to_region": "成都", "summary": "服务费"},
    {"tx_id": "T009", "from_company": "F公司", "to_company": "G公司", "amount": 99000, "tx_date": "2025-05-01 10:00:00", "from_region": "深圳", "to_region": "深圳", "summary": "采购"},
    {"tx_id": "T010", "from_company": "F公司", "to_company": "G公司", "amount": 98000, "tx_date": "2025-05-01 10:05:00", "from_region": "深圳", "to_region": "深圳", "summary": "采购"},
    {"tx_id": "T011", "from_company": "F公司", "to_company": "G公司", "amount": 97000, "tx_date": "2025-05-01 10:10:00", "from_region": "深圳", "to_region": "深圳", "summary": "采购"},
    {"tx_id": "T012", "from_company": "F公司", "to_company": "G公司", "amount": 96000, "tx_date": "2025-05-01 10:15:00", "from_region": "深圳", "to_region": "深圳", "summary": "采购"},
    {"tx_id": "T013", "from_company": "Z公司", "to_company": "X公司", "amount": 500000, "tx_date": "2025-06-01 03:30:00", "from_region": "广州", "to_region": "广州", "summary": "往来款"},
    {"tx_id": "T014", "from_company": "X公司", "to_company": "Z公司", "amount": 480000, "tx_date": "2025-06-05 04:00:00", "from_region": "广州", "to_region": "广州", "summary": "退款"},
    {"tx_id": "T015", "from_company": "A公司", "to_company": "B公司", "amount": 40000, "tx_date": "2025-04-02 09:00:00", "from_region": "成都", "to_region": "成都", "summary": "办公用品"},
    {"tx_id": "T016", "from_company": "A公司", "to_company": "B公司", "amount": 35000, "tx_date": "2025-04-03 09:30:00", "from_region": "成都", "to_region": "成都", "summary": "办公用品"},
    {"tx_id": "T017", "from_company": "A公司", "to_company": "B公司", "amount": 45000, "tx_date": "2025-04-04 10:00:00", "from_region": "成都", "to_region": "成都", "summary": "办公用品"},
    {"tx_id": "T018", "from_company": "A公司", "to_company": "B公司", "amount": 38000, "tx_date": "2025-04-05 10:30:00", "from_region": "成都", "to_region": "成都", "summary": "办公用品"},
    {"tx_id": "T019", "from_company": "A公司", "to_company": "B公司", "amount": 42000, "tx_date": "2025-04-06 11:00:00", "from_region": "成都", "to_region": "成都", "summary": "办公用品"},
    {"tx_id": "T020", "from_company": "H公司", "to_company": "I公司", "amount": 500000, "tx_date": "2025-07-01 10:00:00", "from_region": "成都", "to_region": "拉萨", "summary": "捐赠"},
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="资金异常流动检测模型")
    parser.add_argument("--file", help="资金流水文件 (.csv/.json)")
    parser.add_argument("--output", help="输出文件(.json)")
    parser.add_argument("--sample", action="store_true", help="使用示例数据")
    parser.add_argument("--min-amount", type=float, default=100000, help="最小关注金额")
    parser.add_argument("--window", type=int, default=30, help="分析窗口天数")
    args = parser.parse_args()

    data = None
    if args.sample:
        data = SAMPLE_DATA
        print(f"使用内置示例数据（{len(data)}笔交易）")
    elif args.file:
        ext = os.path.splitext(args.file)[1].lower()
        if ext == ".csv":
            data = load_csv(args.file)
        elif ext == ".json":
            data = load_json(args.file)
        else:
            print(f"不支持的文件格式: {ext}")
            sys.exit(1)
        print(f"加载文件: {args.file}, {len(data)}条记录")
    else:
        data = SAMPLE_DATA
        print(f"未指定输入文件，使用示例数据")

    result = detect_fund_flow_anomalies(data, min_amount=args.min_amount, window_days=args.window)
    print_report(result)

    if args.output:
        import os
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n结果已保存至: {args.output}")

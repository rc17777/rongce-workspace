# -*- coding: utf-8 -*-

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
"""
跨坐标系审计检测工具 (Cross-Coordinate Audit Detection)
=====================================================
基于5个坐标系的交叉验证理念，将可落地的检测方法固化为可执行脚本。

包含5个分析模型：
  M101 出差×考勤时空验证    —— 报销日期 vs 门禁/打卡记录
  M102 受益对象重复检测      —— 同一人/同地址多地多次享受补贴
  M103 进销存三向比对        —— 进货量 vs 库存 vs 销售量逻辑一致
  M104 报价行为模式分析      —— 投标报价的数学规律检测
  M105 时间序列矛盾检测      —— 合同/验收/付款的日期逻辑

使用方式：
  py cross_coordinate_audit.py M101 --file 报销门禁数据.csv
  py cross_coordinate_audit.py M102 --file 受益名单.csv
  py cross_coordinate_audit.py M103 --file 进销存数据.csv
  py cross_coordinate_audit.py M104 --file 投标报价数据.csv
  py cross_coordinate_audit.py M105 --file 采购合同数据.csv
  py cross_coordinate_audit.py sample               # 运行全部示例
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import csv
import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import Counter, defaultdict
import math

SKILL_DIR = Path(__file__).parent

# 导入扩展模块（M106-M108）
from cross_coordinate_audit_ext import (
    M106_SAMPLE, detect_street_view_conflicts,
    M107_SAMPLE, detect_satellite_progress_conflicts,
    M108_SAMPLE, detect_quantity_reverse_conflict,
)
# 导入替代方案模块（M109-M113）
from cross_coordinate_audit_alt import (
    M109_SAMPLE, detect_oa_ip_trip_conflict,
    M111_SAMPLE, detect_voucher_behavior_anomaly, print_m111_report,
    M113_SAMPLE, detect_material_construction_mismatch,
)

# ============================================================
# M101: 出差×考勤时空验证
# 原理：时空坐标系验证。声称X日出差的人，同一天在单位门禁/考勤有记录
# ============================================================

M101_SAMPLE = [
    {"name":"张三","dept":"财务科","trip_start":"2026-03-10","trip_end":"2026-03-14","destination":"北京","amount":4500,
     "attendance_dates":["2026-03-10","2026-03-11","2026-03-12","2026-03-13","2026-03-14"],
     "attendance_records":["08:32 门禁-正门","08:45 门禁-正门","08:30 门禁-侧门","08:40 门禁-正门","08:35 门禁-正门"]},
    {"name":"李四","dept":"办公室","trip_start":"2026-03-08","trip_end":"2026-03-10","destination":"上海","amount":3200,
     "attendance_dates":["2026-03-07","2026-03-11"],
     "attendance_records":["08:30 门禁-正门","08:40 门禁-正门"]},
    {"name":"王五","dept":"业务科","trip_start":"2026-03-01","trip_end":"2026-03-05","destination":"广州","amount":6800,
     "attendance_dates":["2026-02-28","2026-03-06"],
     "attendance_records":["08:30 门禁-正门","08:35 门禁-正门"]},
    {"name":"赵六","dept":"人事科","trip_start":"2026-03-15","trip_end":"2026-03-16","destination":"成都","amount":2800,
     "attendance_dates":["2026-03-15","2026-03-16","2026-03-17"],
     "attendance_records":["08:30 门禁-正门","09:15 门禁-正门","08:30 门禁-正门"]},
    {"name":"孙七","dept":"财务科","trip_start":"2026-03-20","trip_end":"2026-03-22","destination":"深圳","amount":5200,
     "attendance_dates":["2026-03-20"],
     "attendance_records":["08:40 门禁-正门"]},
]

def detect_trip_attendance_conflict(data):
    """检测出差期间是否有考勤/门禁记录"""
    results = []
    for row in data:
        trip_start = datetime.strptime(row["trip_start"], "%Y-%m-%d").date()
        trip_end = datetime.strptime(row["trip_end"], "%Y-%m-%d").date()
        att_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in row.get("attendance_dates", [])]

        # 找出出差期间有考勤的日期
        conflict_dates = [d for d in att_dates if trip_start <= d <= trip_end]
        conflict_records = []
        for i, d in enumerate(att_dates):
            if trip_start <= d <= trip_end:
                conflict_records.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "record": row.get("attendance_records", [])[i] if i < len(row.get("attendance_records", [])) else ""
                })

        if conflict_dates:
            risk = "🔴 高" if len(conflict_dates) >= len(set(d for d in [trip_start + timedelta(days=n) for n in range((trip_end-trip_start).days+1) if d.weekday() < 5])) * 0.7 else "🟡 中"
            results.append({
                "name": row["name"], "dept": row["dept"],
                "trip": "%s~%s (%s)" % (row["trip_start"], row["trip_end"], row["destination"]),
                "amount": row["amount"],
                "conflict_days": len(conflict_dates),
                "total_trip_days": (trip_end - trip_start).days + 1,
                "conflict_details": conflict_records,
                "risk": risk,
                "suggestion": "出差期间有%d天在本单位门禁打卡，建议核实：是否实际出差？是否他人代打卡？出差审批是否真实？" % len(conflict_dates)
            })

    return sorted(results, key=lambda x: x["conflict_days"], reverse=True)


# ============================================================
# M102: 受益对象重复检测
# 原理：时空坐标系验证。同一身份证/同一地址/同一银行账号多次受益
# ============================================================

M102_SAMPLE = [
    {"beneficiary_id":"510101199001011234","name":"张某","address":"成都市锦江区XX路1号","bank_account":"6222024402012345678","subsidy_type":"以旧换新","amount":500,"date":"2026-03-01"},
    {"beneficiary_id":"510101199001011234","name":"张某","address":"成都市锦江区XX路1号","bank_account":"6222024402012345678","subsidy_type":"以旧换新","amount":500,"date":"2026-03-15"},
    {"beneficiary_id":"510101199001011234","name":"张某","address":"成都市锦江区XX路1号","bank_account":"6222024402087654321","subsidy_type":"购新补贴","amount":300,"date":"2026-04-01"},
    {"beneficiary_id":"510101199202021235","name":"李某","address":"成都市武侯区YY路2号","bank_account":"6222024402012345678","subsidy_type":"以旧换新","amount":500,"date":"2026-03-10"},
    {"beneficiary_id":"510101199303031236","name":"王某","address":"成都市锦江区XX路1号","bank_account":"6222024402099999999","subsidy_type":"以旧换新","amount":500,"date":"2026-03-20"},
    {"beneficiary_id":"510101199404041237","name":"赵某","address":"成都市高新区ZZ路4号","bank_account":"6222024402011111111","subsidy_type":"购新补贴","amount":300,"date":"2026-04-05"},
    {"beneficiary_id":"510101199505051238","name":"孙某","address":"成都市金牛区AA路5号","bank_account":"6222024402022222222","subsidy_type":"以旧换新","amount":500,"date":"2026-03-25"},
    {"beneficiary_id":"510101199101011234","name":"张某某","address":"成都市锦江区XX路1号","bank_account":"6222024402012345678","subsidy_type":"以旧换新","amount":500,"date":"2026-05-01"},
]

def detect_duplicate_beneficiaries(data):
    """检测重复受益对象"""
    # 按身份证聚合
    id_groups = defaultdict(list)
    for row in data:
        id_groups[row["beneficiary_id"]].append(row)

    # 按银行账号聚合
    bank_groups = defaultdict(list)
    for row in data:
        bank_groups[row["bank_account"]].append(row)

    # 按地址聚合
    addr_groups = defaultdict(list)
    for row in data:
        addr_groups[row["address"]].append(row)

    results = []
    seen_ids = set()

    # 同身份证多次
    for bid, items in id_groups.items():
        if len(items) > 1:
            names = set(i["name"] for i in items)
            results.append({
                "type": "同身份证",
                "key": bid,
                "count": len(items),
                "names": list(names),
                "name_match": len(names) == 1,
                "details": ["%s %s %s ¥%s" % (i["date"], i["subsidy_type"], i["address"], i["amount"]) for i in items],
                "risk": "🔴 高" if len(items) >= 3 else "🟡 中",
                "suggestion": "同一身份证享受%d次补贴，需核验是否为重复申报或身份冒用" % len(items)
            })
            seen_ids.add(bid)

    # 同银行账号不同身份证
    for bank, items in bank_groups.items():
        ids = set(i["beneficiary_id"] for i in items)
        if len(ids) > 1 and len(items) > 1:
            results.append({
                "type": "同银行账号不同身份证",
                "key": bank,
                "count": len(items),
                "names": list(set(i["name"] for i in items)),
                "name_match": False,
                "details": ["ID:%s %s" % (i["beneficiary_id"], i["name"]) for i in items],
                "risk": "🔴 高",
                "suggestion": "同一银行账号关联%d个不同身份证，可能为团伙操作或账户被冒用" % len(ids)
            })

    # 同地址不同身份证
    for addr, items in addr_groups.items():
        ids = set(i["beneficiary_id"] for i in items)
        if len(ids) >= 3:
            results.append({
                "type": "同地址多身份证",
                "key": addr,
                "count": len(items),
                "names": list(set(i["name"] for i in items)),
                "name_match": False,
                "details": ["ID:%s %s" % (i["beneficiary_id"], i["name"]) for i in items[0:5]],
                "risk": "🟡 中" if len(ids) < 5 else "🔴 高",
                "suggestion": "同一地址关联%d个不同受益人，建议核验是否为虚假地址或集中刷单" % len(ids)
            })

    return sorted(results, key=lambda x: x["count"], reverse=True)


# ============================================================
# M103: 进销存三向比对
# 原理：物理坐标系验证。期初+进货-期末=销量。销量应≥申报补贴销量。
# ============================================================

M103_SAMPLE = [
    {"product":"品牌A空调1.5P","merchant":"XX电器","period":"2026Q1","begin_inventory":50,"purchase":200,"end_inventory":30,"declared_sales":240,"subsidy_amount":120000},
    {"product":"品牌A空调1.5P","merchant":"XX电器","period":"2026Q2","begin_inventory":30,"purchase":150,"end_inventory":20,"declared_sales":170,"subsidy_amount":85000},
    {"product":"品牌B冰箱500L","merchant":"XX电器","period":"2026Q1","begin_inventory":20,"purchase":80,"end_inventory":15,"declared_sales":90,"subsidy_amount":45000},
    {"product":"品牌B冰箱500L","merchant":"XX电器","period":"2026Q2","begin_inventory":15,"purchase":60,"end_inventory":40,"declared_sales":50,"subsidy_amount":25000},
    {"product":"品牌C手机Pro","merchant":"YY数码","period":"2026Q1","begin_inventory":100,"purchase":500,"end_inventory":50,"declared_sales":520,"subsidy_amount":156000},
    {"product":"品牌D洗衣机","merchant":"ZZ家电","period":"2026Q1","begin_inventory":10,"purchase":30,"end_inventory":10,"declared_sales":40,"subsidy_amount":20000},
]

def detect_inventory_sales_gap(data):
    """进销存三向比对：实际可销量 vs 申报销量"""
    results = []
    for row in data:
        begin = float(row["begin_inventory"])
        purchase = float(row["purchase"])
        end = float(row["end_inventory"])
        declared = float(row["declared_sales"])

        # 理论最大可销量 = 期初 + 进货 - 期末
        max_sellable = begin + purchase - end
        gap = declared - max_sellable
        gap_pct = (gap / declared * 100) if declared > 0 else 0

        if gap > 0:
            risk = "🔴 高" if gap_pct > 20 else ("🟡 中" if gap_pct > 5 else "🟢 低")
            results.append({
                "product": row["product"],
                "merchant": row["merchant"],
                "period": row["period"],
                "begin": begin, "purchase": purchase, "end": end,
                "max_sellable": max_sellable,
                "declared": declared,
                "gap": gap,
                "gap_pct": round(gap_pct, 1),
                "risk": risk,
                "suggestion": ("申报销量(%d)超出理论最大可销量(%d)达%d台(%.1f%%)。可能原因："
                              "(1)虚报销量套取补贴；(2)进货记录不完整；(3)库存盘点不实。"
                              "建议核验该商户的进货发票和仓库实际库存。") % (declared, max_sellable, gap, gap_pct)
            })
    return sorted(results, key=lambda x: x["gap_pct"], reverse=True)


# ============================================================
# M104: 报价行为模式分析
# 原理：行为坐标系验证。多家投标报价是否存在人工干预的数学规律。
# ============================================================

M104_SAMPLE = [
    # 正常竞争项目
    {"project":"XX局办公设备采购","bidder":"A公司","bid_amount":985000,"rank":1,"win":True},
    {"project":"XX局办公设备采购","bidder":"B公司","bid_amount":1020000,"rank":2,"win":False},
    {"project":"XX局办公设备采购","bidder":"C公司","bid_amount":1055000,"rank":3,"win":False},
    # 疑似围标项目（等差报价）
    {"project":"YY中心信息化项目","bidder":"D公司","bid_amount":2000000,"rank":1,"win":True},
    {"project":"YY中心信息化项目","bidder":"E公司","bid_amount":2100000,"rank":2,"win":False},
    {"project":"YY中心信息化项目","bidder":"F公司","bid_amount":2200000,"rank":3,"win":False},
    # 疑似精准控价（极小额差）
    {"project":"ZZ街道服务采购","bidder":"G公司","bid_amount":498000,"rank":1,"win":True},
    {"project":"ZZ街道服务采购","bidder":"H公司","bid_amount":502000,"rank":2,"win":False},
    {"project":"ZZ街道服务采购","bidder":"I公司","bid_amount":505000,"rank":3,"win":False},
]

def detect_bidding_pattern(data):
    """检测投标报价行为模式"""
    # 按项目分组
    projects = defaultdict(list)
    for row in data:
        projects[row["project"]].append(row)

    results = []
    for proj, bids in projects.items():
        amounts = sorted([b["bid_amount"] for b in bids])
        if len(amounts) < 3:
            continue

        signals = []

        # 检测1：等差/等比数列
        diffs = [amounts[i+1] - amounts[i] for i in range(len(amounts)-1)]
        if len(set(diffs)) == 1:
            signals.append("等差报价(差=%d)，高度疑似围标" % diffs[0])

        if len(diffs) >= 2:
            ratios = [round(amounts[i+1]/amounts[i], 3) for i in range(len(amounts)-1) if amounts[i] > 0]
            if len(set(ratios)) == 1:
                signals.append("等比报价(比=%.3f)，高度疑似围标" % ratios[0])

        # 检测2：中标价与第二名差距极小（精准控价）
        winner = [b for b in bids if b.get("win")]
        runners = sorted([b for b in bids if not b.get("win")], key=lambda x: x["bid_amount"])
        if winner and runners:
            win_amt = winner[0]["bid_amount"]
            second_amt = runners[0]["bid_amount"]
            gap_pct = (second_amt - win_amt) / second_amt * 100 if second_amt > 0 else 0
            if 0 < gap_pct < 1.0:
                signals.append("中标价仅低于第二名%.1f%%，存在精准控价嫌疑" % gap_pct)

        # 检测3：报价过于集中
        avg = sum(amounts) / len(amounts)
        if avg > 0:
            spread = (max(amounts) - min(amounts)) / avg * 100
            if spread < 3:
                signals.append("报价区间极窄(价差%.1f%%)，缺乏真实竞争" % spread)

        if signals:
            results.append({
                "project": proj,
                "bidder_count": len(bids),
                "amounts": amounts,
                "signals": signals,
                "risk": "🔴 高" if len(signals) >= 2 else "🟡 中",
                "suggestion": "；".join(signals) + "。建议调取投标文件元数据和制作时间进行交叉验证。"
            })

    return results


# ============================================================
# M105: 时间序列矛盾检测
# 原理：时间序列坐标系验证。合同/公告/验收/付款的先后顺序逻辑。
# ============================================================

M105_SAMPLE = [
    {"project":"XX局2026年度物业管理","proc_type":"公开招标","bid_announce_date":"2026-01-10","contract_date":"2026-01-05","acceptance_date":"2026-12-31","payment_date":"2026-02-01","amount":500000},
    {"project":"YY中心设备采购","proc_type":"询价","bid_announce_date":"2026-03-01","contract_date":"2026-03-20","acceptance_date":"2026-03-19","payment_date":"2026-03-21","amount":200000},
    {"project":"ZZ街道装修工程","proc_type":"紧急采购","bid_announce_date":"2026-02-15","contract_date":"2026-02-14","acceptance_date":"2026-05-01","payment_date":"2026-05-02","amount":800000},
    {"project":"AA局咨询服务","proc_type":"竞争性磋商","bid_announce_date":"2026-04-01","contract_date":"2026-04-15","acceptance_date":"2026-07-01","payment_date":"2026-07-15","amount":150000},
    {"project":"BB局印刷服务","proc_type":"直接委托","bid_announce_date":"","contract_date":"2026-03-01","acceptance_date":"2026-03-28","payment_date":"2026-03-01","amount":30000},
]

def detect_time_sequence_conflicts(data):
    """检测时间序列矛盾"""
    results = []
    for row in data:
        signals = []

        contract_date = _parse_date(row.get("contract_date"))
        bid_date = _parse_date(row.get("bid_announce_date"))
        acceptance_date = _parse_date(row.get("acceptance_date"))
        payment_date = _parse_date(row.get("payment_date"))

        # 检测1：合同签订早于招标公告
        if contract_date and bid_date and contract_date < bid_date:
            signals.append("合同签订(%s)早于招标公告(%s)，存在先定后招嫌疑" % (
                row["contract_date"], row["bid_announce_date"]))

        # 检测2：验收日期早于合同签订
        if acceptance_date and contract_date and acceptance_date < contract_date:
            signals.append("验收日期(%s)早于合同签订(%s)，时间逻辑矛盾" % (
                row["acceptance_date"], row["contract_date"]))

        # 检测3：付款日期早于验收
        if payment_date and acceptance_date and payment_date < acceptance_date:
            signals.append("付款日期(%s)早于验收日期(%s)，未验收先付款" % (
                row["payment_date"], row["acceptance_date"]))

        # 检测4：招标到合同签订过短（法定不少于20天）
        if bid_date and contract_date:
            days = (contract_date - bid_date).days
            if row.get("proc_type") == "公开招标" and days < 20:
                signals.append("招标到签订仅%d天（法定≥20天），疑似缩短招标周期" % days)

        # 检测5：验收后当天付款（无审核周期）
        if acceptance_date and payment_date:
            days_to_pay = (payment_date - acceptance_date).days
            if days_to_pay == 0:
                signals.append("验收当天即付款，无正常审核周期")
            elif days_to_pay > 365:
                signals.append("验收后%d天才付款，可能存在质量争议或资金挪用" % days_to_pay)

        if signals:
            results.append({
                "project": row["project"],
                "proc_type": row.get("proc_type", ""),
                "amount": row["amount"],
                "dates": {
                    "招标公告": row.get("bid_announce_date", ""),
                    "合同签订": row.get("contract_date", ""),
                    "验收": row.get("acceptance_date", ""),
                    "付款": row.get("payment_date", "")
                },
                "signals": signals,
                "risk": "🔴 高" if len(signals) >= 2 else "🟡 中",
                "suggestion": "；".join(signals) + "。建议调取完整采购档案核实。"
            })

    return sorted(results, key=lambda x: len(x["signals"]), reverse=True)


def _parse_date(s):
    """尝试多种日期格式"""
    if not s or s.strip() == "":
        return None
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


# ============================================================
# 输出和运行
# ============================================================

MODELS = [
    {"id":"M101","name":"出差×考勤时空验证","func":detect_trip_attendance_conflict,"sample":M101_SAMPLE},
    {"id":"M102","name":"受益对象重复检测","func":detect_duplicate_beneficiaries,"sample":M102_SAMPLE},
    {"id":"M103","name":"进销存三向比对","func":detect_inventory_sales_gap,"sample":M103_SAMPLE},
    {"id":"M104","name":"报价行为模式分析","func":detect_bidding_pattern,"sample":M104_SAMPLE},
    {"id":"M105","name":"时间序列矛盾检测","func":detect_time_sequence_conflicts,"sample":M105_SAMPLE},
    {"id":"M106","name":"街景时空验证","func":detect_street_view_conflicts,"sample":M106_SAMPLE},
    {"id":"M107","name":"卫星图进度验证","func":detect_satellite_progress_conflicts,"sample":M107_SAMPLE},
    {"id":"M108","name":"工程量反推","func":detect_quantity_reverse_conflict,"sample":M108_SAMPLE},
    {"id":"M109","name":"OA登录IPx出差验证","func":detect_oa_ip_trip_conflict,"sample":M109_SAMPLE},
    {"id":"M111","name":"凭证制单行为分析","func":detect_voucher_behavior_anomaly,"sample":M111_SAMPLE,"special_print":"m111"},
    {"id":"M113","name":"材料进场x施工日志","func":detect_material_construction_mismatch,"sample":M113_SAMPLE},
]


def print_report(model, results):
    """格式化输出检测报告"""
    print()
    print("=" * 70)
    print("  %s %s" % (model["id"], model["name"]))
    print("=" * 70)

    if not results:
        print("  ✅ 未发现异常")
        return

    print("  发现 %d 个异常项\n" % len(results))

    for i, r in enumerate(results, 1):
        risk_icon = r.get("risk", "")
        print("  [%d] %s %s" % (i, risk_icon, r.get("type", r.get("project", r.get("product", r.get("name", ""))))))

        if "merchant" in r:
            print("      商户: %s | 周期: %s" % (r["merchant"], r.get("period", "")))
        if "dept" in r and "trip" in r:
            amt = r.get("amount", "")
            amt_str = " | 金额: ¥%s" % amt if amt else ""
            print("      部门: %s | 出差: %s%s" % (r["dept"], r["trip"], amt_str))
        if "conflict_days" in r and "total_trip_days" in r:
            print("      冲突天数: %d/%d" % (r["conflict_days"], r["total_trip_days"]))
        if "conflict_records" in r:
            print("      OA/系统操作明细:")
            for rec in r["conflict_records"]:
                tag = "⚠️" if rec.get("is_high_sensitivity") else "  "
                print("        %s %s %s | %s | %s" % (tag, rec["date"], rec["time"], rec["system"], rec["action"]))
        if "gap" in r:
            print("      理论可销: %d | 申报销量: %d | 缺口: %d (%.1f%%)" % (r["max_sellable"], r["declared"], r["gap"], r["gap_pct"]))
        if "bidder_count" in r:
            print("      报价: %s" % r["amounts"])
        if "count" in r:
            print("      次数: %d | 关联人数: %d" % (r["count"], len(r["names"])))
        if "signals" in r:
            for s in r["signals"]:
                print("      ⚡ %s" % s)
        if "dates" in r:
            print("      日期: %s" % json.dumps(r["dates"], ensure_ascii=False))
        if "conflict_details" in r:
            print("      打卡明细:")
            for d in r["conflict_details"]:
                print("        - %s: %s" % (d["date"], d["record"]))
        if "reversals" in r:
            print("      材料反推:")
            for mat_key, rev in r["reversals"].items():
                flag = "⚠️" if rev["gap_pct"] > 20 else "✅"
                print("        %s %s: %s -> 反推%s=%.0f (%s=%.0f, 差%.1f%%)" % (
                    flag, mat_key, rev["formula"], rev["target"], rev["reversed"],
                    rev["compare_label"], rev["compare_to"], rev["gap_pct"]))
        if "baidu_url" in r and r["baidu_url"]:
            print("      🔗 百度街景: %s" % r["baidu_url"])
        if "query_links" in r:
            print("      📡 卫星查询:")
            for name, link in r["query_links"].items():
                print("        %s: %s" % (name, link[:80] + "..." if len(str(link)) > 80 else link))
        if "manual_steps" in r:
            print("      📋 操作步骤:")
            for step in r["manual_steps"]:
                print("        %s" % step)

        print("      💡 %s" % r["suggestion"])
        print()

    # 统计
    high = sum(1 for r in results if "🔴" in r.get("risk",""))
    mid = sum(1 for r in results if "🟡" in r.get("risk",""))
    low = sum(1 for r in results if "🟢" in r.get("risk",""))
    print("  风险分布: 🔴%d 🟡%d 🟢%d" % (high, mid, low))
    print("=" * 70)


def load_csv(filepath):
    """加载CSV数据"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 数值字段转换
            for k, v in row.items():
                if v and v.replace('.','').replace('-','').isdigit():
                    try:
                        row[k] = float(v) if '.' in v else int(v)
                    except ValueError:
                        pass
            data.append(row)
    return data


def run_sample_all():
    """运行所有示例"""
    for m in MODELS:
        results = m["func"](m["sample"])
        if m.get("special_print") == "m111":
            print_m111_report(results)
        else:
            print_report(m, results)


def run_model(model_id, filepath=None):
    """运行指定模型"""
    m = next((m for m in MODELS if m["id"] == model_id.upper()), None)
    if not m:
        print("未找到模型: %s" % model_id)
        print("可用模型: %s" % ", ".join(mm["id"] for mm in MODELS))
        return

    if filepath:
        data = load_csv(filepath)
    else:
        data = m["sample"]

    results = m["func"](data)
    if m.get("special_print") == "m111":
        print_m111_report(results)
    else:
        print_report(m, results)
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("跨坐标系审计检测工具")
        print("用法:")
        print("  py cross_coordinate_audit.py sample          # 运行全部示例")
        print("  py cross_coordinate_audit.py M101            # 出差×考勤验证（示例）")
        print("  py cross_coordinate_audit.py M101 --file xxx.csv  # 用真实数据")
        for m in MODELS:
            print("  py cross_coordinate_audit.py %s    # %s" % (m["id"], m["name"]))
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd.lower() == "sample":
        run_sample_all()
    elif cmd.upper() in [m["id"] for m in MODELS]:
        filepath = None
        if len(sys.argv) >= 4 and sys.argv[2] == "--file":
            filepath = sys.argv[3]
        run_model(cmd, filepath)
    else:
        print("未知命令: %s" % cmd)
        print("可用: sample | %s" % " | ".join(m["id"] for m in MODELS))

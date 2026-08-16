# -*- coding: utf-8 -*-

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
"""
跨坐标系审计检测工具 - 替代方案模块（M109-M113）
=================================================
M109: OA登录IP x 出差地验证  —— 手机信令替代方案
M111: 凭证制单行为分析          —— 审批行为画像替代方案
M113: 材料进场 x 施工日志验证   —— 探地雷达替代方案（第一层）
"""

from datetime import datetime, date, timedelta
from collections import defaultdict
import math, json

def _parse_date_any(s):
    if not s or str(s).strip() == "":
        return None
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


# ============================================================
# M109: OA登录IP x 出差地验证
# 手机信令替代方案：用OA/财务系统登录IP来代替运营商信令
# 原理：声称在X地出差的人，同一天用内网IP登录了单位系统
# ============================================================

M109_SAMPLE = [
    # 正常：出差期间无内网操作
    {"name":"张三","dept":"财务科","trip_start":"2026-03-10","trip_end":"2026-03-14",
     "destination":"北京","login_records":[
         {"date":"2026-03-09","time":"08:30","ip":"10.10.1.100","system":"OA","action":"审批报销"},
         {"date":"2026-03-15","time":"08:45","ip":"10.10.1.100","system":"OA","action":"查看通知"},
     ]},
    # 异常：出差期间从公司内网IP登录OA操作业务
    {"name":"李四","dept":"办公室","trip_start":"2026-03-08","trip_end":"2026-03-12",
     "destination":"上海","login_records":[
         {"date":"2026-03-08","time":"14:30","ip":"10.10.1.50","system":"OA","action":"发起采购审批"},
         {"date":"2026-03-10","time":"09:15","ip":"10.10.1.50","system":"OA","action":"审批合同"},
         {"date":"2026-03-11","time":"16:00","ip":"10.10.1.50","system":"财务系统","action":"制单"},
     ]},
    # 混合：部分异常
    {"name":"王五","dept":"业务科","trip_start":"2026-03-01","trip_end":"2026-03-05",
     "destination":"广州","login_records":[
         {"date":"2026-03-02","time":"10:00","ip":"10.10.1.88","system":"OA","action":"查看文件"},
         {"date":"2026-03-03","time":"14:00","ip":"114.25.13.xx","system":"OA","action":"查看文件"},
     ]},
    # 异常：出差期间操作了财务系统（比OA登录更可疑）
    {"name":"赵六","dept":"采购部","trip_start":"2026-03-20","trip_end":"2026-03-22",
     "destination":"深圳","login_records":[
         {"date":"2026-03-20","time":"09:00","ip":"10.10.2.30","system":"财务系统","action":"制单"},
         {"date":"2026-03-21","time":"10:30","ip":"10.10.2.30","system":"财务系统","action":"审核凭证"},
         {"date":"2026-03-22","time":"08:30","ip":"10.10.2.30","system":"OA","action":"审批付款"},
     ]},
]

# 内网IP特征（10.x, 172.16-31.x, 192.168.x）
LOCAL_IP_PATTERNS = ["10.", "172.16.", "172.17.", "172.18.", "172.19.",
                     "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                     "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                     "172.30.", "172.31.", "192.168."]

def _is_local_ip(ip):
    """判断是否为内网IP"""
    if not ip:
        return False
    for prefix in LOCAL_IP_PATTERNS:
        if ip.startswith(prefix):
            return True
    return False

# 高敏感系统操作（比普通OA登录更可疑）
HIGH_SENSITIVITY_ACTIONS = ["制单", "审核凭证", "记账", "审批付款", "审批报销",
                             "修改凭证", "删除凭证", "过账", "结账"]

def detect_oa_ip_trip_conflict(data):
    """
    OA登录IP x 出差地时空验证

    替代原理（手机信令的替代方案）：
    声称出差期间，从单位内网IP登录OA/财务系统进行操作 →
    要么人在公司（虚假出差），要么账号被他人使用（内控漏洞）。

    证据强度分级：
    - 内网IP + OA浏览 → 弱信号（可能VPN远程接入）
    - 内网IP + OA审批操作 → 中信号（远程审批合理但存疑）
    - 内网IP + 财务系统制单/审核 → 强信号（财务操作必须内网）
    """
    results = []
    for row in data:
        trip_start = _parse_date_any(row.get("trip_start"))
        trip_end = _parse_date_any(row.get("trip_end"))
        login_records = row.get("login_records", [])

        if not trip_start or not trip_end:
            continue

        conflict_records = []
        has_finance_op = False
        has_oa_op = False
        trip_dates = set()
        d = trip_start
        while d <= trip_end:
            trip_dates.add(d)
            d += timedelta(days=1)

        for rec in login_records:
            rec_date = _parse_date_any(rec.get("date"))
            ip = rec.get("ip", "")
            system = rec.get("system", "")
            action = rec.get("action", "")

            if rec_date and rec_date in trip_dates:
                is_local = _is_local_ip(ip)
                is_high_sensitivity = any(a in action for a in HIGH_SENSITIVITY_ACTIONS)

                if is_local:
                    conflict_records.append({
                        "date": rec["date"],
                        "time": rec["time"],
                        "ip": ip,
                        "system": system,
                        "action": action,
                        "is_high_sensitivity": is_high_sensitivity
                    })
                    if system == "财务系统" or is_high_sensitivity:
                        has_finance_op = True
                    if system == "OA":
                        has_oa_op = True

        if conflict_records:
            # 风险判定
            if has_finance_op:
                risk = "🔴 高"
                risk_reason = "出差期间从内网IP操作财务系统，几乎可确认人不在出差地"
            elif has_oa_op and len(conflict_records) >= 2:
                risk = "🟡 中"
                risk_reason = "出差期间多次从内网IP操作OA，建议核实：VPN远程？他人代操作？"
            else:
                risk = "🟡 中"
                risk_reason = "出差期间有内网操作记录，建议核实操作背景"

            results.append({
                "name": row["name"],
                "dept": row["dept"],
                "trip": "%s~%s (%s)" % (row["trip_start"], row["trip_end"], row["destination"]),
                "total_trip_days": (trip_end - trip_start).days + 1,
                "conflict_days": len(set(r["date"] for r in conflict_records)),
                "conflict_count": len(conflict_records),
                "has_finance_op": has_finance_op,
                "conflict_records": conflict_records,
                "risk": risk,
                "suggestion": risk_reason + "。建议：(1)核实IP确认为内网的证据；(2)与被审计人确认是否本人操作；(3)如是他人操作，追查账号共享和权限管理漏洞。"
            })

    return sorted(results, key=lambda x: (x["has_finance_op"], x["conflict_count"]), reverse=True)


# ============================================================
# M111: 凭证制单行为分析
# 审批行为画像替代方案：从财务凭证元数据分析异常制单行为
# 原理：不需要OA日志，序时账本身就包含了足够的行为信息
# ============================================================

M111_SAMPLE = [
    {"voucher_id":"J-2026-001","maker":"张三","make_date":"2026-01-05","make_time":"08:45",
     "auditor":"李四","audit_date":"2026-01-06","audit_time":"10:00",
     "booker":"王五","book_date":"2026-01-06","amount":50000,"summary":"办公设备采购"},
    {"voucher_id":"J-2026-002","maker":"张三","make_date":"2026-01-05","make_time":"08:50",
     "auditor":"李四","audit_date":"2026-01-06","audit_time":"10:05",
     "booker":"王五","book_date":"2026-01-06","amount":30000,"summary":"办公设备采购"},
    {"voucher_id":"J-2026-003","maker":"张三","make_date":"2026-01-12","make_time":"22:15",
     "auditor":"张三","audit_date":"2026-01-12","audit_time":"22:16",
     "booker":"张三","book_date":"2026-01-12","amount":150000,"summary":"工程款支付"},
    {"voucher_id":"J-2026-004","maker":"赵六","make_date":"2026-01-15","make_time":"17:55",
     "auditor":"赵六","audit_date":"2026-01-15","audit_time":"17:56",
     "booker":"赵六","book_date":"2026-01-15","amount":80000,"summary":"咨询服务费"},
    {"voucher_id":"J-2026-005","maker":"张三","make_date":"2026-01-20","make_time":"14:30",
     "auditor":"李四","audit_date":"2026-01-21","audit_time":"09:00",
     "booker":"王五","book_date":"2026-01-21","amount":20000,"summary":"差旅费报销"},
    {"voucher_id":"J-2026-006","maker":"孙七","make_date":"2026-02-28","make_time":"23:45",
     "auditor":"李四","audit_date":"2026-03-01","audit_time":"08:30",
     "booker":"王五","book_date":"2026-03-01","amount":120000,"summary":"预付工程款"},
    {"voucher_id":"J-2026-007","maker":"张三","make_date":"2026-03-05","make_time":"16:50",
     "auditor":"张三","audit_date":"2026-03-05","audit_time":"16:51",
     "booker":"张三","book_date":"2026-03-05","amount":500000,"summary":"大额支出"},
    {"voucher_id":"J-2026-008","maker":"周八","make_date":"2026-03-09","make_time":"09:00",
     "auditor":"李四","audit_date":"2026-03-09","audit_time":"09:05",
     "booker":"王五","book_date":"2026-03-09","amount":10000,"summary":"办公用品"},
]

def detect_voucher_behavior_anomaly(data):
    """
    凭证制单行为分析

    替代原理（审批行为画像的替代方案）：
    从序时账提取行为信号，不需要OA日志：

    1. 一人多角色：制单/审核/记账同人 → 内控失效
    2. 深夜/周末制单：非工作时间的操作 → 异常动机
    3. 审核秒批：制单→审核间隔<5分钟 → 审核走过场
    4. 大额单人操作：高金额+一人多角色 → 高风险组合
    5. 集中制单：同一人短时间内密集制单 → 可能为突击补单
    6. 月末/季末集中：在财务节点集中操作 → 突击花钱/调节账目
    """
    results = []
    anomalies = []

    # 按制单人分组
    maker_groups = defaultdict(list)
    for row in data:
        maker_groups[row["maker"]].append(row)

    for row in data:
        voucher_id = row.get("voucher_id", "")
        maker = row.get("maker", "")
        auditor = row.get("auditor", "")
        booker = row.get("booker", "")
        make_time = row.get("make_time", "")
        audit_time = row.get("audit_time", "")
        amount = float(row.get("amount", 0))
        make_date = _parse_date_any(row.get("make_date"))
        signals = []

        # 信号1：制单/审核/记账同一人
        roles = set()
        if maker: roles.add(maker)
        if auditor: roles.add(auditor)
        if booker: roles.add(booker)
        if len(roles) == 1 and len([x for x in [maker, auditor, booker] if x]) >= 2:
            signals.append("🔴 制单/审核/记账同一人(%s)，内控完全失效" % list(roles)[0])
        elif len(roles) == 2 and len([x for x in [maker, auditor, booker] if x]) == 3:
            signals.append("🟡 制单/审核/记账仅2人(%s)，未实现三岗分离" % "/".join(sorted(roles)))

        # 信号2：深夜/周末制单
        if make_time:
            try:
                t = datetime.strptime(make_time, "%H:%M").time()
                if t.hour >= 22 or t.hour < 6:
                    signals.append("🔴 深夜制单(%s)，异常操作时段" % make_time)
                elif t.hour >= 20:
                    signals.append("🟡 晚间制单(%s)" % make_time)
                if make_date and make_date.weekday() >= 5:
                    signals.append("🟡 周末制单(%s是周%d)" % (row.get("make_date",""), make_date.weekday()+1))
            except:
                pass

        # 信号3：审核秒批（与"即验即付"同类逻辑）
        if make_time and audit_time and maker != auditor:
            try:
                t1 = datetime.strptime(make_time, "%H:%M")
                t2 = datetime.strptime(audit_time, "%H:%M")
                diff_min = (t2 - t1).total_seconds() / 60
                if 0 <= diff_min < 5:
                    signals.append("🟡 审核秒批(制单后仅%.0f分钟即审核)，审核走过场嫌疑" % diff_min)
            except:
                pass

        # 信号4：大额+单人全流程
        if amount >= 100000 and len(roles) == 1:
            signals.append("🔴 大额(%.0f万)+单人全流程，高风险" % (amount/10000))

        # 信号5：月末集中制单
        if make_date and amount >= 50000:
            if make_date.day >= 25:
                signals.append("🟡 月末制单(%d日)+大额(%.0f万)" % (make_date.day, amount/10000))

        if signals:
            anomaly = {
                "voucher_id": voucher_id,
                "maker": maker,
                "auditor": auditor,
                "booker": booker,
                "make_date": row.get("make_date",""),
                "make_time": make_time,
                "amount": amount,
                "summary": row.get("summary",""),
                "roles_count": len(roles),
                "signals": signals,
                "risk": "🔴 高" if any("🔴" in s for s in signals) else "🟡 中",
            }
            anomalies.append(anomaly)

    # 统计层面的异常：制单人集中度
    maker_stats = {}
    for maker, items in maker_groups.items():
        total_amt = sum(float(i.get("amount",0)) for i in items)
        unaudited = sum(1 for i in items if i.get("maker") == i.get("auditor"))
        maker_stats[maker] = {
            "count": len(items),
            "total_amount": total_amt,
            "self_audit_ratio": round(unaudited/len(items)*100, 1) if items else 0
        }

    return {
        "anomalies": sorted(anomalies, key=lambda x: x["amount"], reverse=True),
        "maker_stats": maker_stats
    }


def print_m111_report(results):
    """M111专用输出格式"""
    anomalies = results.get("anomalies", [])
    maker_stats = results.get("maker_stats", {})

    print()
    print("=" * 70)
    print("  M111 凭证制单行为分析")
    print("=" * 70)

    if not anomalies:
        print("  ✅ 未发现异常制单行为")
        return

    print("  发现 %d 个异常凭证\n" % len(anomalies))

    for i, a in enumerate(anomalies, 1):
        print("  [%d] %s %s" % (i, a["risk"], a["voucher_id"]))
        print("      制单:%s(%s %s) 审核:%s 记账:%s" % (
            a["maker"], a["make_date"], a["make_time"], a["auditor"], a["booker"]))
        print("      金额: ¥%.0f | 摘要: %s" % (a["amount"], a["summary"]))
        print("      角色数: %d人覆盖全流程" % a["roles_count"])
        for s in a["signals"]:
            print("      ⚡ %s" % s)
        print()

    # 制单人统计
    print("  ── 制单人行为画像 ──")
    for maker, stats in sorted(maker_stats.items(), key=lambda x: x[1]["total_amount"], reverse=True):
        flag = "⚠️" if stats["self_audit_ratio"] > 30 else "✅"
        print("  %s %s: %d笔, ¥%.0f万, 自审率%.0f%%" % (
            flag, maker, stats["count"], stats["total_amount"]/10000, stats["self_audit_ratio"]))

    high = sum(1 for a in anomalies if "🔴" in a["risk"])
    mid = sum(1 for a in anomalies if "🟡" in a["risk"])
    print("\n  异常凭证风险分布: 🔴%d 🟡%d" % (high, mid))
    print("=" * 70)


# ============================================================
# M113: 材料进场 x 施工日志交叉验证
# 探地雷达替代方案（第一层：零成本文书交叉）
# 原理：施工日志记录的工程活动 vs 材料进场记录的实物支撑
# ============================================================

M113_SAMPLE = [
    # 正常：材料进场量与施工日志匹配
    {"project":"XX安置房1#楼","date":"2025-04-10",
     "construction_log":"浇筑三层柱C30混凝土, 方量85m³, 8:00-16:00",
     "material_delivery":[
         {"material":"C30商品混凝土","quantity":90,"unit":"m³","delivery_time":"2025-04-10 07:30","supplier":"XX商混站","ticket_no":"HN20250410-001"},
         {"material":"C30商品混凝土","quantity":0,"unit":"m³","delivery_time":"","supplier":"","ticket_no":""},
     ]},
    # 异常：施工日志说浇筑了120m³，但当天商混站送货单只有50m³
    {"project":"YY学校体育馆","date":"2025-05-15",
     "construction_log":"浇筑二层梁板C35混凝土, 方量120m³, 7:00-18:00",
     "material_delivery":[
         {"material":"C35商品混凝土","quantity":50,"unit":"m³","delivery_time":"2025-05-15 08:00","supplier":"YY商混站","ticket_no":"HN20250515-001"},
         {"material":"C35商品混凝土","quantity":0,"unit":"m³","delivery_time":"","supplier":"","ticket_no":""},
     ]},
    # 异常：施工活动日当天完全没有材料进场记录
    {"project":"ZZ道路工程","date":"2025-06-20",
     "construction_log":"铺设水稳层, 面积2000m², 使用水泥80吨, 砂石300m³, 6:00-19:00",
     "material_delivery":[]},
    # 正常：材料在施工前送达（提前备料）
    {"project":"AA水库加固","date":"2025-07-01",
     "construction_log":"坝体灌浆, 水泥用量15吨, 8:00-17:00",
     "material_delivery":[
         {"material":"P.O42.5水泥","quantity":15,"unit":"吨","delivery_time":"2025-06-29 14:00","supplier":"AA水泥厂","ticket_no":"SN20250629-003"},
     ]},
    # 异常：大量钢筋拉走但施工日志没对应记录
    {"project":"BB桥梁工程","date":"2025-07-10",
     "construction_log":"绑扎桥墩钢筋, 使用HRB400钢筋约8吨",
     "material_delivery":[
         {"material":"HRB400钢筋Φ25","quantity":3,"unit":"吨","delivery_time":"2025-07-10 07:00","supplier":"BB钢铁","ticket_no":"GJ20250710-001"},
         {"material":"HRB400钢筋Φ25","quantity":0,"unit":"吨","delivery_time":"","supplier":"","ticket_no":""},
     ]},
]


def detect_material_construction_mismatch(data):
    """
    材料进场 x 施工日志交叉验证

    替代原理（探地雷达的第一层替代方案）：
    不需要物理检测设备，只需交叉比对两类文书：
    - 施工日志：记录了每天做了什么、用了多少材料
    - 材料进场记录：商混站发货单、钢材送货单、水泥送货单等

    逻辑：如果施工日志声称某天做了X，需要的材料量是Y，
    但当天（或合理提前期内）材料进场记录总量远小于Y →
    施工日志造假。

    三层递进：
    1. 当天进场量 vs 施工日志声称用量 → 直接矛盾
    2. 提前3天进场总量 vs 施工日志声称用量 → 备料合理性
    3. 整个施工周期材料总量 vs 设计图纸计算量 → M108已覆盖
    """
    results = []

    # 材料消耗参考系数（每单位工程活动所需的材料量）
    CONSUMPTION_REF = {
        "C30": {"混凝土": 1.0},  # 1m³工程=1m³混凝土
        "C35": {"混凝土": 1.0},
        "水稳层": {"水泥": 0.04, "砂石": 0.15},  # 吨/m², m³/m² (估算)
    }

    for row in data:
        log_text = str(row.get("construction_log", ""))
        log_date = _parse_date_any(row.get("date"))
        deliveries = row.get("material_delivery", [])

        signals = []

        # 从施工日志提取关键数字
        import re
        concrete_match = re.search(r'(\d+)\s*m[³3]', log_text)
        area_match = re.search(r'(\d+)\s*m[²2]', log_text)
        steel_match = re.search(r'钢筋.*?(\d+)\s*吨', log_text)
        cement_match = re.search(r'水泥.*?(\d+)\s*吨', log_text)

        claimed_concrete = float(concrete_match.group(1)) if concrete_match else 0
        claimed_area = float(area_match.group(1)) if area_match else 0
        claimed_steel = float(steel_match.group(1)) if steel_match else 0

        # 统计当天及前3天材料进场总量
        total_delivery = defaultdict(float)
        same_day_delivery = defaultdict(float)

        for d in deliveries:
            material = d.get("material", "")
            quantity = float(d.get("quantity", 0))
            delivery_time = d.get("delivery_time", "")
            del_date = _parse_date_any(delivery_time.split(" ")[0] if delivery_time else "")

            if del_date and log_date:
                days_before = (log_date - del_date).days
                if 0 <= days_before <= 3:
                    # 归类材料
                    if "混凝土" in material:
                        total_delivery["混凝土"] += quantity
                        if days_before == 0:
                            same_day_delivery["混凝土"] += quantity
                    if "钢筋" in material:
                        total_delivery["钢筋"] += quantity
                        if days_before == 0:
                            same_day_delivery["钢筋"] += quantity
                    if "水泥" in material:
                        total_delivery["水泥"] += quantity
                        if days_before == 0:
                            same_day_delivery["水泥"] += quantity
                    if "砂" in material:
                        total_delivery["砂石"] += quantity
                        if days_before == 0:
                            same_day_delivery["砂石"] += quantity

        # 混凝土用量验证
        if claimed_concrete > 0:
            if total_delivery["混凝土"] == 0:
                signals.append("🔴 施工日志记录浇筑%.0fm³混凝土，但当天及前3天均无混凝土进场记录" % claimed_concrete)
            elif total_delivery["混凝土"] < claimed_concrete * 0.8:
                signals.append("🟡 施工日志要求%.0fm³，但近3天仅进场%.0fm³(差%.0f%%)" % (
                    claimed_concrete, total_delivery["混凝土"],
                    (1 - total_delivery["混凝土"]/claimed_concrete)*100))

        # 钢筋用量验证
        if claimed_steel > 0:
            if total_delivery["钢筋"] == 0:
                signals.append("🔴 施工日志记录使用%.0f吨钢筋，但无对应进场记录" % claimed_steel)
            elif total_delivery["钢筋"] < claimed_steel * 0.7:
                signals.append("🟡 施工日志需要%.0f吨钢筋，实际进场仅%.0f吨(差%.0f%%)" % (
                    claimed_steel, total_delivery["钢筋"],
                    (1 - total_delivery["钢筋"]/claimed_steel)*100))

        # 通用检查：施工日志有活动但当天完全无材料进场
        if not deliveries:
            signals.append("🟡 施工日志有施工活动但当天无任何材料进场记录，建议核实材料来源")

        if signals:
            results.append({
                "project": row["project"],
                "date": row.get("date",""),
                "construction_log": log_text[:80],
                "total_concrete_delivered": total_delivery["混凝土"],
                "total_steel_delivered": total_delivery["钢筋"],
                "claimed_concrete": claimed_concrete,
                "claimed_steel": claimed_steel,
                "signals": signals,
                "risk": "🔴 高" if any("🔴" in s for s in signals) else "🟡 中",
                "suggestion": "；".join(signals) + "。建议：(1)调取商混站/钢材供应商的原始发货单核对；(2)核对监理日志同一天的记录；(3)如确认矛盾，此为施工日志造假的直接证据。"
            })

    return sorted(results, key=lambda x: len(x["signals"]), reverse=True)

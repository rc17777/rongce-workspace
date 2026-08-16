# -*- coding: utf-8 -*-

import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
"""
跨坐标系审计检测工具 - 扩展模块（M106-M108）
=============================================
M106: 街景时空验证 —— 验收照片×地图历史影像比对
M107: 卫星图进度验证 —— 卫星/航拍影像×申报施工进度
M108: 工程量反推 —— 材料用量×工程量数学关系
"""

from datetime import datetime, date, timedelta
from collections import defaultdict
import math, json

# ============================================================
# M106: 街景时空验证（照片×地图历史影像比对）
# ============================================================

M106_SAMPLE = [
    {"evidence_id":"E001","project":"XX路市政绿化工程","photo_date":"2025-08-15",
     "photo_location":"成都市锦江区XX路与YY路交叉口","lat":30.6598,"lng":104.0634,
     "claimed_scene":"绿化带已完成种植，苗木高度约1.5米","acceptance_date":"2025-08-16","amount":800000},
    {"evidence_id":"E002","project":"YY小区改造","photo_date":"2025-03-10",
     "photo_location":"成都市武侯区ZZ街12号","lat":30.5728,"lng":104.0679,
     "claimed_scene":"外墙翻新已完成","acceptance_date":"2025-03-11","amount":1200000},
    {"evidence_id":"E003","project":"AA产业园道路建设","photo_date":"2025-06-20",
     "photo_location":"成都市高新区BB路100号","lat":30.5148,"lng":104.0451,
     "claimed_scene":"沥青路面铺设完成","acceptance_date":"2025-06-20","amount":3500000},
    {"evidence_id":"E004","project":"CC河道治理","photo_date":"2024-11-01",
     "photo_location":"成都市金牛区CC河段","lat":30.6921,"lng":104.0523,
     "claimed_scene":"河堤加固完成","acceptance_date":"2024-11-05","amount":2500000},
    {"evidence_id":"E005","project":"DD中学操场翻新","photo_date":"2025-01-20",
     "photo_location":"成都市成华区DD路50号","lat":30.6593,"lng":104.1091,
     "claimed_scene":"塑胶跑道铺设完成","acceptance_date":"2025-01-18","amount":600000},
]


def _parse_date_any(s):
    """尝试多种日期格式"""
    if not s or str(s).strip() == "":
        return None
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def detect_street_view_conflicts(data):
    """
    街景时空验证
    
    原理：验收/现场照片的拍摄时间和地点，可通过地图街景历史影像独立验证。
    百度地图时光机覆盖2013-2025年的街景数据。
    
    本函数输出：(1)风险预判信号 (2)按经纬度生成一键查询链接 (3)人工比对检查清单
    """
    results = []
    now = date.today()

    for row in data:
        signals = []
        photo_date = _parse_date_any(row.get("photo_date"))
        acceptance_date = _parse_date_any(row.get("acceptance_date"))
        lat = row.get("lat")
        lng = row.get("lng")

        # 预判1：照片日期早于验收日期太多（可能是旧照片凑数）
        if photo_date and acceptance_date:
            days_before = (acceptance_date - photo_date).days
            if days_before > 30:
                signals.append("照片拍摄(%s)比验收日期(%s)早%d天，可能为历史旧照片" % (
                    row["photo_date"], row["acceptance_date"], days_before))
            elif days_before < 0:
                signals.append("照片拍摄日期晚于验收日期，时间逻辑矛盾")

        # 预判2：冬季/雨季拍摄的室外工程验收照片——施工条件存疑
        if photo_date:
            month = photo_date.month
            if month in [12, 1, 2]:
                signals.append("照片拍摄于冬季(%d月)，室外工程的施工进度和绿化效果存疑" % month)
            if month in [6, 7, 8] and "沥青" in str(row.get("claimed_scene", "")):
                pass  # 夏季适合沥青铺设

        # 预判3：高危信号——验收与照片同一天（可能是临时摆拍）
        if photo_date and acceptance_date:
            diff = abs((acceptance_date - photo_date).days)
            if diff <= 1:
                signals.append("验收与照片拍摄几乎同天(%d天差)，需核验是否为验收当天临时布置的摆拍场景" % diff)

        # 生成查询链接
        bd_url = ""
        if lat and lng:
            bd_url = "https://map.baidu.com/@%.6f,%.6f,21z" % (lat, lng)

        if signals:
            results.append({
                "evidence_id": row["evidence_id"],
                "project": row["project"],
                "amount": row["amount"],
                "photo_date": row.get("photo_date", ""),
                "acceptance_date": row.get("acceptance_date", ""),
                "location": row.get("photo_location", ""),
                "claimed_scene": row.get("claimed_scene", ""),
                "baidu_url": bd_url,
                "signals": signals,
                "risk": "🔴 高" if len(signals) >= 2 else "🟡 中",
                "suggestion": "打开百度地图时光机URL，选择照片日期前后的历史影像，对比现场实际状态。%s" % (
                    "重点关注：是否存在建设痕迹、植被/建筑外观是否与照片一致。" if not signals else ""
                ),
                "manual_steps": [
                    "1. 打开浏览器访问: %s" % bd_url,
                    "2. 点击右下角'时光机'图标",
                    "3. 选择照片日期(%s)前后的时间点" % row.get("photo_date", ""),
                    "4. 对比街景中的实际场景与照片描述的差异",
                    "5. 截图存档作为审计证据",
                ]
            })

    return sorted(results, key=lambda x: len(x["signals"]), reverse=True)


# ============================================================
# M107: 卫星图进度验证
# ============================================================

M107_SAMPLE = [
    {"project":"XX路市政道路","milestone":"路基完成","claimed_date":"2025-03-31",
     "satellite_before":"2025-01-15","satellite_after":"2025-04-10",
     "claimed_progress_pct":60,"paid_amount":5000000,"total_budget":12000000,
     "location":"成都市XX区","lat":30.65,"lng":104.06,
     "visible_change_expected":"道路路基轮廓应明显可见"},
    {"project":"YY安置房建设","milestone":"主体封顶","claimed_date":"2025-06-30",
     "satellite_before":"2025-04-01","satellite_after":"2025-07-15",
     "claimed_progress_pct":80,"paid_amount":25000000,"total_budget":40000000,
     "location":"成都市YY区","lat":30.57,"lng":104.07,
     "visible_change_expected":"建筑主体结构应完整显现"},
    {"project":"ZZ工业园区","milestone":"场地平整","claimed_date":"2025-02-28",
     "satellite_before":"2024-12-01","satellite_after":"2025-03-15",
     "claimed_progress_pct":40,"paid_amount":8000000,"total_budget":30000000,
     "location":"成都市ZZ区","lat":30.51,"lng":104.04,
     "visible_change_expected":"场地应有明显平整痕迹，土方开挖可见"},
    {"project":"AA水库加固","milestone":"坝体加固","claimed_date":"2025-05-15",
     "satellite_before":"2025-03-01","satellite_after":"2025-06-01",
     "claimed_progress_pct":50,"paid_amount":6000000,"total_budget":15000000,
     "location":"成都市AA乡","lat":30.70,"lng":104.20,
     "visible_change_expected":"坝体附近应有施工痕迹（设备、材料堆放、道路拓宽）"},
]


def detect_satellite_progress_conflicts(data):
    """
    卫星图进度验证
    
    原理：用不同时期的卫星/航拍影像比对施工区域的实际变化，
    与申报进度和已支付工程款进行交叉验证。
    
    数据源：
    - Google Earth 历史影像（免费，需手动操作）
    - 天地图 历史影像（国内数据源）
    - Sentinel-2 卫星（10m分辨率，免费，每5天过境）
    - 如有无人机航拍则精度更高
    
    本函数输出：风险预判信号 + 卫星影像查询指引 + 比对检查项
    """
    results = []
    for row in data:
        signals = []
        claimed_date = _parse_date_any(row.get("claimed_date"))
        before_date = _parse_date_any(row.get("satellite_before"))
        after_date = _parse_date_any(row.get("satellite_after"))
        progress = float(row.get("claimed_progress_pct", 0))
        paid = float(row.get("paid_amount", 0))
        total = float(row.get("total_budget", 1))

        # 预判1：进度申报vs付款比例不匹配
        pay_ratio = (paid / total * 100) if total > 0 else 0
        progress_gap = pay_ratio - progress
        if abs(progress_gap) > 20:
            direction = "超付" if progress_gap > 0 else "低报进度"
            signals.append("%s：付款比例(%.1f%%) vs 申报进度(%.1f%%)，差额%.1f%%" % (
                direction, pay_ratio, progress, progress_gap))

        # 预判2：卫星影像前后间隔是否合理
        if before_date and after_date:
            interval = (after_date - before_date).days
            if interval < 30:
                signals.append("前后卫星影像间隔仅%d天，施工变化可能不明显，建议拉长比对周期" % interval)
            if interval > 180:
                signals.append("前后卫星影像间隔%d天(>180天)，期间可能有多阶段变化，需分段比对" % interval)

        # 预判3：申报的关键节点vs季节——不合适施工的季节
        if claimed_date:
            m = claimed_date.month
            if m in [12, 1, 2] and any(kw in str(row.get("milestone","")).lower() for kw in ["混凝土","浇筑","封顶"]):
                signals.append("冬季(%d月)申报混凝土相关节点，低温可能影响施工质量" % m)

        # 生成查询指引
        lat = row.get("lat")
        lng = row.get("lng")
        query_links = {}
        if lat and lng:
            query_links["Google Earth"] = "打开Google Earth Pro → 输入坐标 %.4f,%.4f → 点击'历史影像'图标 → 选择 %s 和 %s 对比" % (
                lat, lng, row.get("satellite_before",""), row.get("satellite_after",""))
            query_links["天地图"] = "https://www.tianditu.gov.cn/ → 搜索坐标 → 历史影像功能"
            query_links["Sentinel Hub"] = "https://apps.sentinel-hub.com/eo-browser/ → 搜索坐标 → 选择Sentinel-2 → 时间范围 %s~%s" % (
                row.get("satellite_before",""), row.get("satellite_after",""))

        results.append({
            "project": row["project"],
            "milestone": row["milestone"],
            "claimed_date": row.get("claimed_date",""),
            "claimed_progress_pct": progress,
            "pay_ratio_pct": round(pay_ratio, 1),
            "paid_amount": paid,
            "total_budget": total,
            "location": row.get("location",""),
            "visible_change_expected": row.get("visible_change_expected",""),
            "satellite_before": row.get("satellite_before",""),
            "satellite_after": row.get("satellite_after",""),
            "query_links": query_links,
            "signals": signals,
            "risk": "🔴 高" if len(signals) >= 2 else ("🟡 中" if len(signals) == 1 else "🟢 待验证"),
            "suggestion": "通过卫星历史影像比对施工区域的实际变化，核实申报进度是否真实。重点关注：%s" % row.get("visible_change_expected",""),
            "manual_steps": [
                "1. 打开Google Earth Pro（免费软件）",
                "2. 输入项目坐标搜索",
                "3. 使用工具栏'显示历史图像'功能",
                "4. 分别查看 %s 和 %s 的卫星影像" % (row.get("satellite_before",""), row.get("satellite_after","")),
                "5. 对比两个时间点的实际变化",
                "6. 将卫星截图与项目申报进度进行比对",
                "7. 如实际变化明显小于申报进度→虚报进度、超付工程款的信号",
            ]
        })

    return results


# ============================================================
# M108: 工程量反推
# ============================================================

# 工程量反推系数表（行业经验值）
# 注意：以下系数为通用参考值，实际项目需根据设计图纸和施工方案调整
REVERSE_COEFFICIENTS = {
    "混凝土": {"unit": "m³", "target": "建筑面积", "divisor": 0.35, "formula": "混凝土(m3) / 0.35", "note": "框架结构约0.3-0.4m3/m2"},
    "钢筋": {"unit": "吨", "target": "建筑面积", "divisor": 0.045, "formula": "钢筋(t) / 0.045", "note": "框架结构约40-50kg/m2"},
    "水泥": {"unit": "吨", "target": "混凝土量", "divisor": 0.3, "formula": "水泥(t) / 0.3", "note": "C30混凝土约需300kg水泥/m3"},
    "砂石": {"unit": "m³", "target": "混凝土量", "divisor": 0.8, "formula": "砂石(m3) / 0.8", "note": "1m3混凝土约需0.8m3砂石料"},
    "土方开挖": {"unit": "m³", "target": "地下室面积", "divisor": 4.0, "formula": "土方(m3) / 4(开挖深度)", "note": "默认开挖深度4m,需根据实际地勘报告调整"},
    "沥青": {"unit": "吨", "target": "道路面积", "divisor": 0.12, "formula": "沥青(t) / 0.12", "note": "10cm厚面层约需0.12吨/m2"},
    "塑胶跑道": {"unit": "m²", "target": "跑道面积", "divisor": 1.0, "formula": "1:1直接反推", "note": "材料面积=实际铺设面积"},
    "苗木": {"unit": "株", "target": "绿化面积", "divisor": 30, "formula": "苗木(株) / 30株/亩", "note": "乔木约25-36株/亩(按30株算),1亩=666.67m2"},
}

M108_SAMPLE = [
    # 正常项目：材料用量与申报面积匹配
    {"project":"XX安置房1#楼","structure_type":"框架结构","declared_area":15000,
     "materials":{"混凝土(m³)":4800,"钢筋(吨)":620,"水泥(吨)":1550,"砂石(m³)":4200},
     "settlement_amount":45000000,"period":"2024-2025"},
    # 正常项目
    {"project":"YY学校教学楼","structure_type":"框架结构","declared_area":8000,
     "materials":{"混凝土(m³)":2800,"钢筋(吨)":360,"水泥(吨)":900,"砂石(m³)":2400},
     "settlement_amount":24000000,"period":"2024-2025"},
    # 异常：申报道路面积虚高。沥青反推35000但申报50000(差30%)，水泥/砂石反推混凝土量与申报面积不对应
    {"project":"ZZ市政道路","structure_type":"沥青路面+水稳基层","declared_area":50000,
     "materials":{"沥青(吨)":4200,"混凝土(m³)":3000,"水泥(吨)":800,"砂石(m³)":9000},
     "settlement_amount":18000000,"period":"2025"},
    # 异常：绿化面积虚高。苗木450株最多对应约15亩=10000m2，却申报30000m2
    {"project":"AA公园绿化","structure_type":"景观绿化(含园路)","declared_area":30000,
     "materials":{"苗木(株)":450,"混凝土(m³)":200,"水泥(吨)":80,"砂石(m³)":180},
     "settlement_amount":5000000,"period":"2025"},
]


def detect_quantity_reverse_conflict(data):
    """
    工程量反推验证
    
    原理：建筑材料消耗量与实际工程量之间存在物理上的数学关系。
    如果结算申报的工程量远超材料所能支撑的物理极限，说明存在虚报。
    
    反推逻辑：
    1. 根据每种材料用量 → 反推合理的工程量范围
    2. 多种材料反推结果交叉验证 → 互相印证
    3. 反推面积 vs 申报面积 → 计算差距
    """
    results = []
    for row in data:
        materials = row.get("materials", {})
        declared_area = float(row.get("declared_area", 0))
        structure = row.get("structure_type", "")

        reversals = {}
        conflict_count = 0

        for mat_name, amount in materials.items():
            amount = float(amount)
            mat_key = mat_name.replace("(m\u00b3)","").replace("(吨)","").replace("(株)","").replace("(m\u00b2)","")
            coeff = REVERSE_COEFFICIENTS.get(mat_key)

            if not coeff:
                continue

            # 根据系数反推
            target = coeff["target"]
            divisor = coeff["divisor"]
            reversed_amount = amount / divisor if divisor > 0 else 0

            # 不同目标物用不同的申报值对比
            if target == "建筑面积":
                compare_to = declared_area
                compare_label = "申报面积"
            elif target == "混凝土量":
                # 用实际的混凝土(m3)作为对比基准
                compare_to = float(materials.get("混凝土(m³)", 0) or materials.get("混凝土(m3)", 0))
                compare_label = "实际混凝土量"
            elif target == "道路面积":
                compare_to = declared_area
                compare_label = "申报道路面积"
            elif target == "绿化面积":
                compare_to = declared_area
                compare_label = "申报绿化面积"
            else:
                compare_to = declared_area
                compare_label = "申报值"

            if compare_to > 0:
                gap = compare_to - reversed_amount
                gap_pct = (gap / compare_to * 100)
            else:
                # 无对比基准（如混凝土量目标但材料清单无混凝土），跳过
                continue

            reversals[mat_key] = {
                "amount": amount,
                "unit": coeff["unit"],
                "reversed": round(reversed_amount, 0),
                "target": target,
                "compare_to": round(compare_to, 0),
                "compare_label": compare_label,
                "gap": round(gap, 0),
                "gap_pct": round(gap_pct, 1),
                "formula": coeff["formula"],
                "note": coeff["note"],
            }

            if abs(gap_pct) > 20:
                conflict_count += 1

        # 汇总每种材料的反推结论
        high_conflict_items = []
        for mat_key, rev in reversals.items():
            if abs(rev["gap_pct"]) > 20:
                high_conflict_items.append(
                    "%s反推%s=%.0f, %s=%.0f, 差%.1f%%" % (
                        mat_key, rev["target"], rev["reversed"],
                        rev["compare_label"], rev["compare_to"], rev["gap_pct"]))

        # 综合风险判定
        risk = "🟢 低"
        if conflict_count >= 3:
            risk = "🔴 高"
        elif conflict_count >= 1:
            risk = "🟡 中"

        results.append({
            "project": row["project"],
            "structure_type": structure,
            "declared_area": declared_area,
            "settlement_amount": row["settlement_amount"],
            "reversals": reversals,
            "conflict_count": conflict_count,
            "total_material_types": len(reversals),
            "high_conflict_items": high_conflict_items,
            "risk": risk,
            "suggestion": "%d/%d种材料的反推工程量与申报不符。%s" % (
                conflict_count, len(reversals),
                "多种材料交叉印证申报面积虚高，建议实地核验建筑面积。" if conflict_count >= 2
                else "需核实材料采购记录的完整性和真实性。" if conflict_count == 1
                else "材料用量与申报面积基本匹配。")
        })

    return sorted(results, key=lambda x: x["conflict_count"], reverse=True)

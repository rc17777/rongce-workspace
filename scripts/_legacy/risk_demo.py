#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融策·风控规则引擎 — 采购风控模块 Demo 脚本
基于校服采购项目（TQ-CG-(2025)093）实战数据
用途：客户演示 / 端到端验证

输出：
  - risk_ledger.json    风险台账（所有规则触发结果）
  - risk_dashboard.json 全息画像数据
  - 控制台输出分级预警摘要
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# 配置
# ============================================================
PROJECT_NAME = "校服采购项目（TQ-CG-(2025)093）"
BIDDER_COUNT = 5
DATA_DIR = Path(__file__).parent.parent / "output" / "校服分析"
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "demo-output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 术语翻译映射表
# ============================================================
TERM_MAP = {
    "price_pattern": "报价规律异常",
    "tfidf_similarity": "标书文本雷同度",
    "image_hash_collision": "投标文件嵌入图片重复",
    "metadata_source_match": "文件元数据同源",
    "printer_scanner_match": "扫描设备同源",
    "supplier_network": "供应商关联网络",
    "bid_price_deviation": "采购价格偏离度",
}

RISK_LEVEL = {
    "iron_evidence": {"label": "🔴 红色预警", "description": "铁证层规则触发，需立即启动核查"},
    "strong_signal": {"label": "🟡 黄色预警", "description": "强信号层规则触发，建议限期自查"},
    "info":          {"label": "🟢 绿色提示", "description": "辅助层规则触发，列入观察清单"},
}


# ============================================================
# 规则定义
# ============================================================
RULES = [
    {
        "id": "PR-A01",
        "name": "报价规律异常",
        "category": "采购与供应链",
        "level": "iron_evidence",
        "method": "等差数列/阶梯分布/极差异常检测",
        "threshold_desc": "报价呈等差数列或极差异常",
        "result": "pass",
        "detail": "3家有效报价（645/685/695元），差额[40,10]，非等差数列，极差7.8%，正常范围内",
        "score": 10,
    },
    {
        "id": "PR-A03",
        "name": "标书文本雷同",
        "category": "采购与供应链",
        "level": "iron_evidence",
        "method": "TF-IDF向量化 + 余弦相似度矩阵",
        "threshold_desc": "相似度 ≥80% 为高度可疑",
        "result": "pass",
        "detail": "4家两两对比最高相似度36.5%（牧森vs苏美达），远低于80%阈值。段落级1.000匹配均为标准承诺函模板",
        "score": 15,
    },
    {
        "id": "PR-A04",
        "name": "嵌入图片/资源重复",
        "category": "采购与供应链",
        "level": "iron_evidence",
        "method": "图片MD5/SHA256哈希碰撞",
        "threshold_desc": "跨投标人图片哈希相同",
        "result": "pass",
        "detail": "1095张嵌入图片，0跨公司MD5重复",
        "score": 5,
    },
    {
        "id": "PR-A05",
        "name": "标书元数据同源",
        "category": "采购与供应链",
        "level": "strong_signal",
        "method": ".docx core.xml Author/Creator/AppVersion提取",
        "threshold_desc": "WPS版本GUID后缀一致",
        "result": "warn",
        "detail": "4/4投标人WPS build号完全一致（12.1.0.22529_F1E327BC...）。可能是广泛分发的同一版本，建议进一步核实",
        "score": 30,
        "recommendation": "核查4家投标人是否使用同一台电脑或同一标书制作服务商",
    },
    {
        "id": "PR-A07",
        "name": "扫描设备同源",
        "category": "采购与供应链",
        "level": "strong_signal",
        "method": "PDF Producer/Creator字段提取",
        "threshold_desc": "多家扫描设备型号一致",
        "result": "pass",
        "detail": "牧森→RICOH Pro 8120S（高端生产型），苏美达→KONICA MINOLTA bizhub C558（办公一体机），不同品牌型号",
        "score": 10,
    },
]


# ============================================================
# 风险计算
# ============================================================
def compute_risk_summary(rules):
    """计算综合风险评分和统计"""
    total_score = 0
    max_score = 0
    red_count = yellow_count = green_count = 0

    for r in rules:
        max_score += r["score"]
        if r["level"] == "iron_evidence" and r["result"] == "warn":
            total_score += r["score"] * 2  # 铁证触发加权
            red_count += 1
        elif r["level"] == "strong_signal" and r["result"] == "warn":
            total_score += r["score"]
            yellow_count += 1
        elif r["result"] == "warn":
            total_score += r["score"] // 2
            yellow_count += 1
        elif r["result"] == "pass":
            green_count += 1

    risk_pct = min(100, int(total_score / max_score * 100)) if max_score > 0 else 0

    if risk_pct >= 60:
        overall_level = "[RED] 高风险"
    elif risk_pct >= 30:
        overall_level = "[YELLOW] 中风险"
    else:
        overall_level = "[GREEN] 低风险"

    return {
        "project": PROJECT_NAME,
        "bidders": BIDDER_COUNT,
        "rules_run": len(rules),
        "overall_score": risk_pct,
        "overall_level": overall_level,
        "red_alerts": red_count,
        "yellow_alerts": yellow_count,
        "green_info": green_count,
        "generated_at": datetime.now().isoformat(),
    }


def build_risk_ledger(rules, summary):
    """构建风险台账"""
    ledger = {
        "header": summary,
        "rules": [],
    }
    for r in rules:
        entry = {
            "rule_id": r["id"],
            "rule_name": r["name"],
            "category": r["category"],
            "risk_level": RISK_LEVEL[r["level"]]["label"],
            "result": "⚠️ 异常" if r["result"] == "warn" else "✅ 正常",
            "detail": r["detail"],
            "recommendation": r.get("recommendation", ""),
            "method": r["method"],
        }
        ledger["rules"].append(entry)
    return ledger


def build_dashboard_data(rules, summary):
    """构建全息画像Dashboard数据"""
    by_category = {}
    for r in rules:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "warn": 0, "rules": []}
        by_category[cat]["total"] += 1
        if r["result"] == "warn":
            by_category[cat]["warn"] += 1
        by_category[cat]["rules"].append({"id": r["id"], "name": r["name"], "result": r["result"]})

    return {
        "project": PROJECT_NAME,
        "summary": summary,
        "risk_by_category": by_category,
    }


# ============================================================
# 输出
# ============================================================
def print_summary(summary):
    """控制台打印摘要"""
    print()
    print("=" * 60)
    print(f"  融策·风控规则引擎 — 采购风控检测报告")
    print("=" * 60)
    print(f"  项目：{summary['project']}")
    print(f"  投标人数量：{summary['bidders']} 家")
    print(f"  运行规则：{summary['rules_run']} 条")
    print(f"  综合风险评分：{summary['overall_score']}/100  {summary['overall_level']}")
    print("-" * 60)
    print(f"  [RED]  红色预警：{summary['red_alerts']} 条")
    print(f"  [YEL]  黄色预警：{summary['yellow_alerts']} 条")
    print(f"  [GRN]  绿色提示：{summary['green_info']} 条")
    print("-" * 60)

    for r in RULES:
        status = "[!] 异常" if r["result"] == "warn" else "[v] 正常"
        print(f"  [{r['id']}] {r['name']}: {status}")
        if r["result"] == "warn":
            print(f"       → {r['detail'][:80]}...")
            if r.get("recommendation"):
                print(f"       → 建议：{r['recommendation']}")
    print("=" * 60)
    print()


def main():
    summary = compute_risk_summary(RULES)

    # 输出风险台账
    ledger = build_risk_ledger(RULES, summary)
    ledger_path = OUTPUT_DIR / "risk_ledger.json"
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)
    print(f"[OK] 风险台账已输出：{ledger_path}")

    # 输出Dashboard数据
    dashboard = build_dashboard_data(RULES, summary)
    dashboard_path = OUTPUT_DIR / "risk_dashboard.json"
    with open(dashboard_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    print(f"[OK] 全息画像数据已输出：{dashboard_path}")

    # 控制台摘要
    print_summary(summary)

    return summary


if __name__ == "__main__":
    main()

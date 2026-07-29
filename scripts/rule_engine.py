#!/usr/bin/env python3
"""
交叉验证规则引擎 v1.0
基于文章2-Agent03：费用交叉验证三规则 + 扩展规则
纯Python规则引擎，零LLM调用，直接匹配条件输出异常。
"""

import sys, os, json, argparse, csv
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── 规则定义 ──────────────────────────────────────────

RULES = {
    "R01_薪酬员工匹配": {
        "id": "R01",
        "name": "薪酬-员工人数匹配度",
        "source": "文章2-Agent03·规则1",
        "severity": "P1",
        "condition": {
            "metric": "薪酬变动率/员工变动率",
            "formula": "ABS((薪酬总额-上年薪酬)/上年薪酬 - (员工人数-上年人数)/上年人数) > 0.3",
            "explanation": "薪酬增速显著快于员工增速，可能虚列人头或异常加薪"
        },
        "input_fields": ["薪酬总额", "上年薪酬总额", "员工人数", "上年员工人数"],
        "verify": "检查工资表：离职人员是否仍在列、编外人员、一人多岗重复计薪",
        "output_template": "薪酬总额同比增长{delta_salary:.1%}，员工人数同比增长{delta_staff:.1%}，薪酬增速超出员工增速{excess:.1%}个百分点。可能存在虚列人头/非正常加薪。需核实：①工资表中离职人员是否仍在列；②是否存在编外人员计入；③是否存在一人多岗重复计薪。"
    },
    "R02_办公费规模联动": {
        "id": "R02",
        "name": "办公费-营收联动异常",
        "source": "文章2-Agent03·规则2",
        "severity": "P1",
        "condition": {
            "metric": "办公费率变动率",
            "formula": "ABS((办公费/营收-上年办公费/上年营收)/(上年办公费/上年营收)) > 0.5",
            "explanation": "营收未变但办公费暴涨，可能虚列费用"
        },
        "input_fields": ["办公费", "上年办公费", "不含税营收", "上年不含税营收"],
        "verify": "检查办公费大额报销凭证的真实性、合理性",
        "output_template": "办公费率由{old_rate:.2%}增至{new_rate:.2%}，变动{change:.1%}。营收增长仅{rev_growth:.1%}。可能存在虚列办公费。需核实：①大额办公用品采购发票真伪；②是否存在与业务规模不匹配的采购；③是否存在拆分报销规避审批。"
    },
    "R03_在建工程转固": {
        "id": "R03",
        "name": "在建工程长期挂账",
        "source": "文章2-Agent03·规则3",
        "severity": "P0",
        "condition": {
            "metric": "在建工程余额/本期增加额",
            "formula": "在建工程科目余额/本期增加额 > 2 AND 本期减少额=0",
            "explanation": "在建工程余额是当期新增的2倍以上且无转固，可能延迟转固规避折旧"
        },
        "input_fields": ["在建工程余额", "在建工程本期增加额", "在建工程本期减少额"],
        "verify": "实地查看项目是否已完工并投入使用",
        "output_template": "在建工程余额{balance:.0f}万元，本期增加{addition:.0f}万元，余额/增加比={ratio:.1f}倍。本期减少额为0，无任何转固。可能存在在建工程长期挂账、规避计提折旧问题。需核实：①实地考察项目是否已完工投入使用；②已完工项目是否达到预定可使用状态；③如已投入使用是否应补提折旧。"
    },
    "R04_差旅费人均异常": {
        "id": "R04",
        "name": "差旅费人均异常",
        "source": "扩展规则",
        "severity": "P2",
        "condition": {
            "metric": "人均差旅费同比变动",
            "formula": "ABS((差旅费/员工人数-上年差旅费/上年员工人数)/(上年差旅费/上年员工人数)) > 0.5",
            "explanation": "人均差旅费异常波动，关注真实性"
        },
        "input_fields": ["差旅费", "上年差旅费", "员工人数", "上年员工人数"],
        "verify": "抽查差旅费报销凭证：出差审批/行程/住宿的匹配性",
        "output_template": "人均差旅费由{old_per:.0f}元/人增至{new_per:.0f}元/人，增长{change:.1%}。需核实：①抽查差旅报销凭证的出差审批单完整性；②行程与住宿发票时间地点是否一致；③是否存在以差旅名义报销其他费用。"
    },
    "R05_招待费营收比": {
        "id": "R05",
        "name": "招待费-营收比例异常",
        "source": "扩展规则",
        "severity": "P2",
        "condition": {
            "metric": "招待费率变动+绝对值对比",
            "formula": "招待费率同比增幅>50% AND 招待费率>行业均值2倍",
            "explanation": "招待费增速远超营收且费率偏高"
        },
        "input_fields": ["招待费", "上年招待费", "不含税营收", "上年不含税营收"],
        "verify": "检查招待费审批流程、招待对象、招待标准",
        "output_template": "招待费增长{delta:.1%}，营收增长{rev_growth:.1%}，招待费率{rate:.2%}。招待费增速远超营收增速。需核实：①招待审批单完整性（招待对象/人数/标准）；②是否存在个人消费公款报销；③是否违反八项规定精神。"
    },
    "R06_咨询服务费营收比": {
        "id": "R06",
        "name": "咨询服务费异常增长",
        "source": "扩展规则",
        "severity": "P1",
        "condition": {
            "metric": "咨询费/营收比变动",
            "formula": "ABS((咨询费/营收-上年咨询费/上年营收)/(上年咨询费/上年营收)) > 0.8 AND 咨询费>10万",
            "explanation": "咨询服务费异常增长，可能虚开发票套取资金"
        },
        "input_fields": ["咨询服务费", "上年咨询服务费", "不含税营收", "上年不含税营收"],
        "verify": "检查咨询合同+服务成果+付款凭证的完整链条",
        "output_template": "咨询服务费由{old_amount:.0f}万增至{new_amount:.0f}万，增长{delta:.1%}。营收增长仅{rev_growth:.1%}。需核实：①咨询合同是否真实（服务内容/成果/定价）；②是否存在关联方控制的咨询公司；③咨询成果是否可验证。"
    },
    "R07_投资概算执行偏差": {
        "id": "R07",
        "name": "投资概算执行偏差（>10%）",
        "source": "工程竣工财务决算·扩展规则",
        "severity": "P0",
        "condition": {
            "metric": "概算执行率",
            "formula": "ABS(实际完成投资/批复概算 - 1) > 0.1",
            "explanation": "超概10%以上且未见审批文件"
        },
        "input_fields": ["实际完成投资", "批复概算"],
        "verify": "核对超概审批文件·超概原因分析·是否履行调整程序",
        "output_template": "概算批复{approval:.0f}万元，实际完成投资{actual:.0f}万元，超概{excess:.0f}万元（{rate:.1%}）。需核实：①超概是否经过审批（提供审批文件）；②超概原因；③是否履行概算调整程序。"
    },
    "R08_资金平衡表校验": {
        "id": "R08",
        "name": "资金平衡表不平衡",
        "source": "工程竣工财务决算·扩展规则",
        "severity": "P0",
        "condition": {
            "metric": "资金来源-资金占用差额",
            "formula": "ABS(资金来源合计 - 资金占用合计) > 0.01",
            "explanation": "资金平衡表不平"
        },
        "input_fields": ["资金来源合计", "资金占用合计"],
        "verify": "检查科目归集是否正确·是否存在漏记/重记",
        "output_template": "资金平衡表不平！来源合计{src:.2f}万元 vs 占用合计{dst:.2f}万元，差额{diff:.2f}万元。需核实：①科目归集是否正确；②是否存在漏记或重记；③资金来源与占用的科目对应关系。"
    },
    "R09_待摊投资分摊异常": {
        "id": "R09",
        "name": "待摊投资占比过高",
        "source": "工程竣工财务决算·扩展规则",
        "severity": "P1",
        "condition": {
            "metric": "待摊投资/建安投资比",
            "formula": "待摊投资总额/建筑安装工程投资 > 0.15",
            "explanation": "待摊投资占比超过15%"
        },
        "input_fields": ["待摊投资总额", "建筑安装工程投资"],
        "verify": "逐项检查待摊投资的构成·有无多计/错计·分摊方法是否合理",
        "output_template": "待摊投资{apportioned:.0f}万元占建安投资{construction:.0f}万元的{ratio:.1%}，超过15%一般水平。需核实：①待摊投资的具体构成；②有无不应计入的费用（如已列入其他科目的重复费用）；③分摊方法是否合理。"
    },
    "R10_交付使用资产其他项": {
        "id": "R10",
        "name": "交付使用资产-其他项占比异常",
        "source": "工程竣工财务决算·扩展规则",
        "severity": "P1",
        "condition": {
            "metric": "交付资产-其他/交付资产总计",
            "formula": "交付使用资产-其他/交付使用资产总计 > 0.1",
            "explanation": "交付使用资产中'其他'项占比超10%"
        },
        "input_fields": ["交付资产其他", "交付资产总计"],
        "verify": "查看'其他'的具体构成·是否有不应计入的支出",
        "output_template": "交付使用资产中'其他'项{other:.0f}万元占比{ratio:.1%}（通常应<10%）。需核实：①其他项的具体内容；②是否有不应计入交付使用资产的费用被归集到此；③是否需要重分类到具体资产科目。"
    },
    "R11_建设单位管理费": {
        "id": "R11",
        "name": "建设单位管理费超限额",
        "source": "工程竣工财务决算·扩展规则（财建[2016]504号）",
        "severity": "P1",
        "condition": {
            "metric": "管理费-限额比对",
            "formula": "建设单位管理费 > 限额（需手动设置limit字段）",
            "explanation": "管理费超规定限额"
        },
        "input_fields": ["建设单位管理费", "管理费限额"],
        "verify": "检查超支审批·有无不应计入管理费的支出",
        "output_template": "建设单位管理费{actual:.0f}万元，超过限额{limit:.0f}万元，超支{excess:.0f}万元（{rate:.1%}）。需核实：①超支是否经过审批；②是否有不应计入管理费的其他支出被归集；③管理费计算的基数是否准确。"
    }
}


def check_rule(rule_id: str, values: dict) -> Optional[dict]:
    """检查单条规则，返回异常结果或None"""
    rule = RULES[rule_id]
    
    if rule_id == "R01_薪酬员工匹配":
        s0, s1 = values.get("薪酬总额", 0), values.get("上年薪酬总额", 1)
        st0, st1 = values.get("员工人数", 0), values.get("上年员工人数", 1)
        if st1 == 0: return None
        delta_s = (s0 - s1) / s1 if s1 else 0
        delta_st = (st0 - st1) / st1
        if abs(delta_s - delta_st) > 0.3:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    delta_salary=delta_s, delta_staff=delta_st,
                    excess=abs(delta_s - delta_st) * 100
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R02_办公费规模联动":
        of0, of1 = values.get("办公费", 0), values.get("上年办公费", 1)
        rev0, rev1 = values.get("不含税营收", 0), values.get("上年不含税营收", 1)
        if rev0 == 0 or rev1 == 0: return None
        old_rate, new_rate = of1 / rev1, of0 / rev0
        if old_rate == 0: return None
        change = (new_rate - old_rate) / old_rate
        if abs(change) > 0.5:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    old_rate=old_rate, new_rate=new_rate, change=change,
                    rev_growth=(rev0-rev1)/rev1
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R03_在建工程转固":
        bal = values.get("在建工程余额", 0)
        add = values.get("在建工程本期增加额", 1)
        dec = values.get("在建工程本期减少额", -1)
        if add == 0: return None
        ratio = bal / add
        if ratio > 2 and dec == 0:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    balance=bal, addition=add, ratio=ratio
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R04_差旅费人均异常":
        tr0, tr1 = values.get("差旅费", 0), values.get("上年差旅费", 1)
        st0, st1 = values.get("员工人数", 0), values.get("上年员工人数", 1)
        if st0 == 0 or st1 == 0: return None
        old_per, new_per = tr1/st1, tr0/st0
        if old_per == 0: return None
        change = (new_per - old_per) / old_per
        if abs(change) > 0.5:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    old_per=old_per, new_per=new_per, change=change
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R05_招待费营收比":
        en0, en1 = values.get("招待费", 0), values.get("上年招待费", 1)
        rev0, rev1 = values.get("不含税营收", 0), values.get("上年不含税营收", 1)
        if en1 == 0 or rev1 == 0 or rev0 == 0: return None
        delta = (en0 - en1) / en1
        rate = en0 / rev0
        rev_growth = (rev0 - rev1) / rev1
        if delta > 0.5 and rate > 0.005:  # 招待费率>0.5%视为偏高
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    delta=delta, rate=rate, rev_growth=rev_growth
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R06_咨询服务费营收比":
        co0, co1 = values.get("咨询服务费", 0), values.get("上年咨询服务费", 1)
        rev0, rev1 = values.get("不含税营收", 0), values.get("上年不含税营收", 1)
        if co1 == 0 or rev1 == 0 or rev0 == 0: return None
        old_rate, new_rate = co1/rev1, co0/rev0
        if old_rate == 0: return None
        change = abs((new_rate - old_rate) / old_rate)
        delta = (co0 - co1) / co1 if co1 else 0
        if change > 0.8 and co0 > 10:
            return {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    old_amount=co1, new_amount=co0, delta=delta,
                    rev_growth=(rev0-rev1)/rev1
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R07_投资概算执行偏差":
        actual = values.get("实际完成投资", 0)
        approval = values.get("批复概算", 1)
        if approval == 0: return None
        rate = actual / approval
        if abs(rate - 1) > 0.1:
            excess = actual - approval
            return {
                "rule_id": rule["id"], "rule_name": rule["name"],
                "severity": rule["severity"], "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    actual=actual, approval=approval, excess=excess, rate=rate
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R08_资金平衡表校验":
        src = values.get("资金来源合计", 0)
        dst = values.get("资金占用合计", 0)
        if abs(src - dst) > 0.01:
            return {
                "rule_id": rule["id"], "rule_name": rule["name"],
                "severity": rule["severity"], "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    src=src, dst=dst, diff=abs(src-dst)
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R09_待摊投资分摊异常":
        apportioned = values.get("待摊投资总额", 0)
        construction = values.get("建筑安装工程投资", 1)
        if construction == 0: return None
        ratio = apportioned / construction
        if ratio > 0.15:
            return {
                "rule_id": rule["id"], "rule_name": rule["name"],
                "severity": rule["severity"], "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    apportioned=apportioned, construction=construction, ratio=ratio
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R10_交付使用资产其他项":
        other = values.get("交付资产其他", 0)
        total = values.get("交付资产总计", 1)
        if total == 0: return None
        ratio = other / total
        if ratio > 0.1:
            return {
                "rule_id": rule["id"], "rule_name": rule["name"],
                "severity": rule["severity"], "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    other=other, total=total, ratio=ratio
                ),
                "verify_action": rule["verify"]
            }

    elif rule_id == "R11_建设单位管理费":
        actual = values.get("建设单位管理费", 0)
        limit = values.get("管理费限额", 0)
        if limit == 0: return None
        if actual > limit:
            excess = actual - limit
            rate = excess / limit
            return {
                "rule_id": rule["id"], "rule_name": rule["name"],
                "severity": rule["severity"], "source": rule["source"],
                "detected": True,
                "summary": rule["output_template"].format(
                    actual=actual, limit=limit, excess=excess, rate=rate
                ),
                "verify_action": rule["verify"]
            }

    return None


def load_data_from_dict(data: dict) -> list:
    """从字典加载单行数据"""
    return [data]


def load_data_from_csv(filepath: str) -> list:
    """从CSV加载多行数据（每行一个核算单元：部门/单位/科目）"""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 数字字段转换
            numeric_fields = [
                "薪酬总额", "上年薪酬总额", "员工人数", "上年员工人数",
                "办公费", "上年办公费", "不含税营收", "上年不含税营收",
                "在建工程余额", "在建工程本期增加额", "在建工程本期减少额",
                "差旅费", "上年差旅费", "招待费", "上年招待费",
                "咨询服务费", "上年咨询服务费"
            ]
            for field in numeric_fields:
                if field in row:
                    try:
                        row[field] = float(row[field].replace(',', '').replace(' ', ''))
                    except (ValueError, AttributeError):
                        row[field] = 0
            rows.append(row)
    return rows


def run_all_rules(data_rows: list, rule_ids: list = None) -> dict:
    """对所有数据行运行所有规则"""
    if rule_ids is None:
        rule_ids = list(RULES.keys())
    
    results = {
        "run_time": datetime.now().isoformat(),
        "total_rows": len(data_rows),
        "rules_checked": len(rule_ids),
        "findings": []
    }
    
    for row_idx, row in enumerate(data_rows):
        row_label = row.get("label", row.get("名称", f"行{row_idx+1}"))
        for rule_id in rule_ids:
            finding = check_rule(rule_id, row)
            if finding:
                finding["row_label"] = row_label
                finding["row_index"] = row_idx
                results["findings"].append(finding)
    
    # 按严重程度排序
    severity_order = {"P0": 0, "P1": 1, "P2": 2}
    results["findings"].sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    # 统计
    results["summary"] = {
        "total_findings": len(results["findings"]),
        "P0": sum(1 for f in results["findings"] if f["severity"] == "P0"),
        "P1": sum(1 for f in results["findings"] if f["severity"] == "P1"),
        "P2": sum(1 for f in results["findings"] if f["severity"] == "P2"),
    }
    
    return results


def format_report(results: dict) -> str:
    """生成可读报告"""
    s = results["summary"]
    report = f"""# 交叉验证规则引擎 · 检测报告
**运行时间**：{results['run_time']}
**数据行数**：{results['total_rows']}
**规则数量**：{results['rules_checked']}

## 📊 检测概要
| 等级 | 数量 |
|:-----|:-----|
| 🔴 P0（严重） | {s['P0']} |
| 🟡 P1（重要） | {s['P1']} |
| 🟢 P2（关注） | {s['P2']} |
| **合计** | **{s['total_findings']}** |

---
"""
    if not results["findings"]:
        report += "\n✅ 所有规则检查通过，未发现异常。\n"
        return report

    for f in results["findings"]:
        sev_emoji = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}.get(f["severity"], "⚪")
        report += f"""### {sev_emoji} [{f['severity']}] {f['rule_name']}
**数据行**：{f['row_label']}
**来源**：{f['source']}

{f['summary']}

**建议核实动作**：{f['verify_action']}

---
"""
    return report


# ── CLI入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="交叉验证规则引擎 v1.0")
    parser.add_argument("--type", choices=["cross_validation", "construction", "all"], default="all",
                       help="规则类型: cross_validation(财务费用), construction(在建工程), all(全部)")
    parser.add_argument("--data", help="CSV数据文件路径")
    parser.add_argument("--output", default="output/rule_engine_report.md", help="输出报告路径")
    parser.add_argument("--json", help="JSON数据（用于单条测试）")
    parser.add_argument("--list-rules", action="store_true", help="列出所有规则")
    parser.add_argument("--demo", action="store_true", help="运行演示数据")
    args = parser.parse_args()

    if args.list_rules:
        for rid, rule in RULES.items():
            print(f"[{rule['severity']}] {rule['id']} — {rule['name']}")
            print(f"  公式: {rule['condition']['formula']}")
            print(f"  来源: {rule['source']}\n")
        return

    # 确定要跑的规则
    if args.type == "cross_validation":
        rule_ids = ["R01_薪酬员工匹配", "R02_办公费规模联动", "R04_差旅费人均异常", "R05_招待费营收比", "R06_咨询服务费营收比"]
    elif args.type == "construction":
        rule_ids = ["R03_在建工程转固"]
    else:
        rule_ids = list(RULES.keys())

    # 加载数据
    if args.demo:
        data = [{
            "label": "演示数据-XX部门2025",
            "薪酬总额": 580, "上年薪酬总额": 400,
            "员工人数": 25, "上年员工人数": 26,
            "办公费": 85, "上年办公费": 35,
            "不含税营收": 1200, "上年不含税营收": 1150,
            "在建工程余额": 4500, "在建工程本期增加额": 1500,
            "在建工程本期减少额": 0,
            "差旅费": 52, "上年差旅费": 25,
            "招待费": 18, "上年招待费": 8,
            "咨询服务费": 60, "上年咨询服务费": 15,
        }]
    elif args.json:
        data = [json.loads(args.json)]
    elif args.data:
        data = load_data_from_csv(args.data)
    else:
        print("❌ 请提供 --data 文件路径、--json 数据或 --demo")
        print("CSV列名要求：薪酬总额,上年薪酬总额,员工人数,上年员工人数,办公费,上年办公费,不含税营收,上年不含税营收,在建工程余额,在建工程本期增加额,在建工程本期减少额,差旅费,上年差旅费,招待费,上年招待费,咨询服务费,上年咨询服务费")
        sys.exit(1)

    # 运行
    results = run_all_rules(data, rule_ids)
    report = format_report(results)

    # 输出
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\n📄 报告已保存至：{args.output}")
    
    if results["findings"]:
        sys.exit(1)  # 有发现时退出码1，方便CI流水线判断
    sys.exit(0)


if __name__ == "__main__":
    main()

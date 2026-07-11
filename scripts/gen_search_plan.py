"""
融策学术检索计划生成器 — 每周自动生成知网/万方/维普检索式
========================================================
用法：
  python scripts/gen_search_plan.py                     # 生成本周检索计划
  python scripts/gen_search_plan.py --line 经责审计    # 单业务线
  python scripts/gen_search_plan.py --output docx       # 输出Word文档（预留）
  python scripts/gen_search_plan.py --since 2025        # 限定2025年以后
"""
import sys, json
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")

# ============================================================
# 检索词库：按业务线 + 场景维度
# ============================================================

BUSINESS_SCENARIOS = {
    "经责审计": {
        "core": ["经济责任审计", "离任审计", "领导干部审计"],
        "extended": ["任中审计", "自然资源资产离任审计", "权力运行审计"],
        "scenarios": ["党政机关", "国有企业", "事业单位", "高校", "医院"],
        "methods": ["审计评价指标体系", "经济责任界定", "审计评价方法"],
        "years": "2020-2026",
    },
    "收支审计": {
        "core": ["财政收支审计", "预算收入审计", "决算审计"],
        "extended": ["财政收入质量", "财政支出结构", "非税收入审计"],
        "scenarios": ["地方财政", "部门预算", "转移支付"],
        "methods": ["收支真实性审计", "收入完整性审计"],
        "years": "2020-2026",
    },
    "预算执行": {
        "core": ["预算执行审计", "部门预算审计", "预算管理审计"],
        "extended": ["预算编制审计", "预算调整合规性", "预算绩效审计"],
        "scenarios": ["中央预算", "地方预算", "部门预算"],
        "methods": ["预算执行率", "预算偏离度", "结转结余审计"],
        "years": "2020-2026",
    },
    "专项资金": {
        "core": ["专项资金审计", "专项债审计", "社保资金审计"],
        "extended": ["专项债资金使用", "就业补助资金", "乡村振兴资金", "教育专项资金"],
        "scenarios": ["地方政府专项债", "社保基金", "扶贫资金", "科研经费"],
        "methods": ["资金流向追踪", "专款专用审计", "资金闲置率"],
        "years": "2020-2026",
    },
    "往来款清理": {
        "core": ["往来款项审计", "债权债务清理", "暂付款审计"],
        "extended": ["长期挂账", "往来款清理", "其他应收款审计"],
        "scenarios": ["行政事业单位", "国有企业"],
        "methods": ["账龄分析", "函证替代程序", "坏账认定"],
        "years": "2020-2026",
    },
    "招投标审计": {
        "core": ["招投标审计", "政府采购审计", "围标串标检测"],
        "extended": ["评标专家违规", "投标人关联", "采购程序合规"],
        "scenarios": ["政府采购", "工程项目", "药品采购", "设备采购"],
        "methods": ["投标报价分析", "关联关系挖掘", "文本相似度检测"],
        "years": "2020-2026",
    },
    "国企审计": {
        "core": ["国有企业审计", "国有资产审计", "国企改革审计"],
        "extended": ["国企混合所有制", "国有资产保值增值", "境外投资审计"],
        "scenarios": ["地方国企", "央企", "金融国企"],
        "methods": ["资产负债损益审计", "国企负责人经责", "薪酬审计"],
        "years": "2020-2026",
    },
    "成本效益审计": {
        "core": ["绩效评价", "成本效益审计", "财政支出绩效"],
        "extended": ["事前绩效评估", "成本效益分析", "公共服务绩效"],
        "scenarios": ["项目支出绩效", "部门整体绩效", "政策绩效评价"],
        "methods": ["成本效益分析法", "最低成本法", "标杆管理法"],
        "years": "2020-2026",
    },
    "能源审计": {
        "core": ["能源审计", "资源环境审计", "碳中和审计"],
        "extended": ["节能减排审计", "碳排放审计", "自然资源审计"],
        "scenarios": ["工业企业", "公共机构", "能源企业"],
        "methods": ["能源消耗审计", "碳排放核算", "环保专项资金审计"],
        "years": "2020-2026",
    },
    "工程决算审计": {
        "core": ["竣工决算审计", "工程造价审计", "基本建设审计"],
        "extended": ["工程结算审计", "政府投资项目审计", "全过程跟踪审计"],
        "scenarios": ["政府投资", "PPP项目", "地铁/公路/水利"],
        "methods": ["工程量清单审计", "材料价格审计", "签证变更审计"],
        "years": "2020-2026",
    },
    "预算绩效管理": {
        "core": ["预算绩效管理", "事前绩效评估", "绩效监控"],
        "extended": ["绩效目标管理", "绩效评价结果应用", "部门整体绩效"],
        "scenarios": ["地方财政", "部门预算", "转移支付"],
        "methods": ["绩效指标体系", "绩效评价标准", "绩效审计"],
        "years": "2020-2026",
    },
    "政府补贴审计": {
        "core": ["政府补贴审计", "补助资金审计", "惠农资金审计"],
        "extended": ["财政补贴审计", "以旧换新补贴", "农业补贴审计"],
        "scenarios": ["企业补贴", "农业补贴", "消费补贴"],
        "methods": ["补贴对象认定", "补贴资金流向", "骗取补贴识别"],
        "years": "2020-2026",
    },
}

# ============================================================
# 检索式生成
# ============================================================

def make_cnki_expression(line_name, scenario):
    """生成知网高级检索表达式"""
    s = BUSINESS_SCENARIOS[line_name]
    core = s["core"]
    extras = s.get("methods", [])[:2]
    scenarios = s.get("scenarios", [])[:2]
    
    # 主要检索式：SU = ('核心词1' + '核心词2' + ...)
    main = " OR ".join(f'"{c}"' for c in core)
    # 场景限定
    scene = " OR ".join(f'"{c}"' for c in scenarios) if scenarios else ""
    
    if scene:
        # 不限定场景，只限定主题词，避免遗漏
        return f"SU=({main}) AND 年 BETWEEN ({s['years']})"
    return f"SU=({main}) AND 年 BETWEEN ({s['years']})"


def make_wanfang_expression(line_name, scenario):
    """生成万方检索表达式"""
    s = BUSINESS_SCENARIOS[line_name]
    core = s["core"]
    main = " or ".join(f'"{c}"' for c in core)
    return f"主题:({main}) 年份:{s['years']}"


def make_vip_expression(line_name, scenario):
    """生成维普检索表达式"""
    s = BUSINESS_SCENARIOS[line_name]
    core = s["core"]
    main = " OR ".join(f'"{c}"' for c in core)
    return f"M=({main}) AND Y={s['years'].replace('-',',')}"


def generate_weekly_plan(business_lines=None, since_year=None):
    """生成当周检索计划"""
    if business_lines is None:
        business_lines = list(BUSINESS_SCENARIOS.keys())
    
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())  # 周一
    week_end = week_start + timedelta(days=6)
    
    plan = f"""# 融策学术检索周计划
# 周期: {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}
# 生成时间: {today.strftime('%Y-%m-%d %H:%M')}
# 检索范围: {since_year if since_year else '2020'}年至今
# 数据库: 知网(CNKI) / 万方 / 维普(CQVIP)
# 检索方式: 高级检索 → 专业检索模式
# ============================================================
"""
    
    for line_name in business_lines:
        s = BUSINESS_SCENARIOS[line_name]
        plan += f"\n{'='*70}\n"
        plan += f"## {line_name}\n"
        plan += f"{'='*70}\n\n"
        plan += f"**核心词**: {'、'.join(s['core'])}  |  **扩展词**: {'、'.join(s['extended'])}\n"
        plan += f"**场景**: {'、'.join(s['scenarios'])}  |  **方法**: {'、'.join(s['methods'])}\n\n"
        
        # 知网检索式（主题检索）
        cnki_main = " OR ".join(f'"{c}"' for c in s['core'])
        cnki_ext = " OR ".join(f'"{c}"' for c in s['extended'][:3])
        plan += f"### 知网（CNKI）— 专业检索\n\n"
        plan += f"**基础检索（推荐优先）**：\n"
        plan += f"```\nSU=({cnki_main}) AND 年 BETWEEN ({s['years']})\n"
        plan += f"```\n"
        plan += f"**扩展检索（结果不足时）**：\n"
        plan += f"```\nSU=({cnki_main} OR {cnki_ext}) AND 年 BETWEEN ({s['years']})\n"
        plan += f"```\n"
        plan += f"**场景限定（结果过多时）**：\n"
        scene = " OR ".join(f'"{c}"' for c in s['scenarios'][:2])
        plan += f"```\nSU=({cnki_main}) AND SU=({scene}) AND 年 BETWEEN ({s['years']})\n"
        plan += f"```\n\n"
        
        # 万方检索式
        plan += f"### 万方 — 高级检索\n\n"
        plan += f"```\n主题:({cnki_main}) 年份:{s['years']}\n```\n\n"
        
        # 维普检索式
        v = s['years'].replace('-', ',')
        plan += f"### 维普（CQVIP）— 专业检索\n\n"
        plan += f"```\nM=({cnki_main}) AND Y={v}\n```\n\n"
        
        # 操作建议
        plan += f"**操作建议**:\n"
        plan += f"1. 先跑基础检索，筛选标题相关文章；\n"
        plan += f"2. 结果不足时用扩展检索扩大范围；\n"
        plan += f"3. 结果过多时用场景限定缩小范围；\n"
        plan += f"4. 优先下载：核心期刊、CSSCI、学位论文、会议论文；\n"
        plan += f"5. 每篇下载后标注业务线，按 `{line_name}/` 分类存放。\n\n"
    
    # 进度追踪
    plan += f"{'='*70}\n"
    plan += f"## 进度追踪\n"
    plan += f"{'='*70}\n\n"
    plan += f"| 业务线 | 知网 | 万方 | 维普 | 合计 | 已入库 |\n"
    plan += f"|:--|:--:|:--:|:--:|:--:|:--:|\n"
    for line_name in business_lines:
        plan += f"| {line_name} | — | — | — | — | — |\n"
    
    plan += f"\n---\n"
    plan += f"*融策学术检索计划生成器 v1.0 — 每周自动生成*\n"
    
    return plan


def main():
    import argparse
    parser = argparse.ArgumentParser(description="融策学术检索计划生成器")
    parser.add_argument("--line", type=str, help="单业务线")
    parser.add_argument("--since", type=int, default=2020, help="起始年份")
    parser.add_argument("--output", type=str, help="输出路径")
    
    args = parser.parse_args()
    
    business_lines = [args.line] if args.line else None
    
    plan = generate_weekly_plan(business_lines, args.since)
    
    # 输出到控制台
    print(plan)
    
    # 保存到文件
    today = datetime.now().strftime("%Y%m%d")
    filename = f"学术检索计划_{today}.md"
    if args.output:
        filename = args.output
    
    output_path = WORKSPACE / "knowledge" / "intel_summaries" / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(plan, encoding='utf-8')
    
    print(f"\n💾 已保存: {output_path}")
    print(f"   {len(business_lines or list(BUSINESS_SCENARIOS.keys()))} 条业务线")
    print(f"   3 个数据库 × 2-3 条检索式/数据库 = 约 {len(business_lines or list(BUSINESS_SCENARIOS.keys())) * 3 * 2} 条检索式")


if __name__ == "__main__":
    main()
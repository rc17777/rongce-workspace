#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计报告四步串联复核工作流  v1.0
====================================
当用户说"复核报告"时，自动串联四个环节：

  Step 1 🧠 RAG增强：提取审计主题 → RAG知识库检索法规/案例
  Step 2 🔍 快速复核：本地规则引擎（错别字/金额/日期/格式/一致性）
  Step 3 🎯 深度复核：15维度AI审查框架（生成分级提示词）
  Step 4 🚨 自动告警：P0/P1/P2分级 + 知识缺口检测 + 推送

用法：
  # 单报告复核
  python report_review_workflow.py --file "审计报告.docx"
  python report_review_workflow.py --file "审计报告.docx" --deep
  
  # 目录监控模式（自动检测新报告并复核）
  python report_review_workflow.py --watch "projects/某项目/reports"
  
  # JSON输出（供其他脚本调用）
  python report_review_workflow.py --file "报告.docx" --json
"""
import sys, io, os, re, json, hashlib, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
TZ = timezone(timedelta(hours=8))

# ============================================================
# 配置
# ============================================================
RAG_ENHANCED_SCRIPT = ROOT / 'scripts' / 'report_review_rag_enhanced.py'
WATCH_STATE_FILE = ROOT / '.report_review_state.json'
OUTPUT_DIR = ROOT / 'output' / 'report_reviews'

# ============================================================
# Step 1: RAG增强复核（调用已有脚本）
# ============================================================
def step1_rag_enhanced(file_path: str = None, text: str = None) -> Dict:
    """调用报告复核RAG增强脚本"""
    print("\n" + "─" * 50)
    print("  📚 Step 1/4: RAG知识库增强复核")
    print("─" * 50)
    
    try:
        from report_review_rag_enhanced import enhanced_review, enhanced_review_text
        if file_path:
            return enhanced_review(file_path, use_zhixi=False, use_rag=True)
        else:
            return enhanced_review_text(text, use_zhixi=False, use_rag=True)
    except ImportError:
        # Fallback: run as subprocess
        import subprocess
        cmd = [sys.executable, str(RAG_ENHANCED_SCRIPT), "--json"]
        if file_path:
            cmd.extend(["--file", file_path])
        elif text:
            cmd.extend(["--text", text])
        else:
            return {"error": "No input"}
        cmd.append("--no-zhixi")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr[:500]}


# ============================================================
# Step 2: 快速复核（本地规则引擎）
# ============================================================
def step2_quick_review(text: str) -> Dict:
    """本地快速复核：格式/错别字/金额/日期/一致性"""
    print("\n" + "─" * 50)
    print("  🔍 Step 2/4: 本地快速复核")
    print("─" * 50)
    
    issues = []
    
    # —— 2a. 金额单位混用检查 ——
    has_wan = bool(re.search(r'\d+\.?\d*\s*万', text))
    has_yuan = bool(re.search(r'(?<!万)(?<!亿)\d{4,}\s*元', text))
    if has_wan and has_yuan:
        issues.append({
            'dimension': '金额单位',
            'severity': 'P1',
            'message': '报告同时使用"万元"和"元"为单位，建议统一',
            'context': '检查全文金额单位是否一致',
        })
    
    yuan_pattern = re.findall(r'(\d+\.?\d*)\s*万元', text)
    if yuan_pattern:
        for val in yuan_pattern:
            try:
                v = float(val)
                if v >= 10000:
                    issues.append({
                        'dimension': '金额单位',
                        'severity': 'P2',
                        'message': f'金额 {v} 万元可能应为 {v/10000:.2f} 亿元（≥1亿元时建议用"亿"）',
                        'context': f'匹配: {v}万元',
                    })
                    break  # 只报一次
            except:
                pass
    
    # —— 2b. 日期格式检查 ——
    dates = re.findall(r'\d{4}[年.\-/]\d{1,2}[月.\-/]\d{1,2}', text)
    bad_dates = [d for d in dates if not re.match(r'\d{4}年\d{1,2}月\d{1,2}日', d)]
    if bad_dates:
        issues.append({
            'dimension': '日期格式',
            'severity': 'P2',
            'message': f'发现 {len(bad_dates)} 处非标准日期格式（如使用.-/分隔），建议统一为"YYYY年MM月DD日"',
            'context': f'示例: {bad_dates[:3]}',
        })
    
    # —— 2c. 金额大写/小写一致性 ——
    capital_pattern = re.findall(r'([零壹贰叁肆伍陆柒捌玖拾佰仟万亿]+元整?)', text)
    digit_amounts = re.findall(r'(?:人民币|金额|合计)[：:]\s*(\d+\.?\d*)\s*[元万]', text)
    if capital_pattern and digit_amounts:
        issues.append({
            'dimension': '金额书写',
            'severity': 'P2',
            'message': '报告同时包含中文大写金额和阿拉伯数字金额，建议核对一致性',
            'context': f'大写示例: {capital_pattern[0][:20]}, 数字示例: {digit_amounts[0] if digit_amounts else "N/A"}',
        })
    
    # —— 2d. 常见错别字/不规范用语 ——
    typo_rules = [
        (r'帐', '账', '账务/账户/台账应为"账"'),
        (r'做出(?!了)', '作出', '公文规范用"作出决定/作出处理"'),
        (r'截止(?!到)', '截至', '"截止"不接宾语，"截至"可接宾语'),
        (r'涉及到', '涉及', '"涉及"已含"到"义'),
        (r'来自于', '来自', '"来自"已含"于"义'),
        (r'必须的', '必需的', '"必须"是副词，"必需"是形容词'),
        (r'其它', '其他', '公文规范用"其他"而非"其它"'),
        (r'做为', '作为', '"作为"是规范写法'),
        (r'签定', '签订', '"签订合同"非"签定"'),
        (r'给与', '给予', '"给予"是规范写法'),
    ]
    for pattern, correct, explanation in typo_rules:
        matches = re.findall(pattern, text)
        if matches:
            # 排除一些合法用法（如"帐"在专有名词中）
            context_matches = []
            for m in re.finditer(pattern, text):
                ctx = text[max(0,m.start()-10):m.end()+10]
                if pattern == r'帐' and any(kw in ctx for kw in ['帐篷','蚊帐']):
                    continue
                context_matches.append(m.group())
            if context_matches:
                issues.append({
                    'dimension': '错别字',
                    'severity': 'P1' if len(context_matches) > 3 else 'P2',
                    'message': f'{explanation} — 发现 {len(context_matches)} 处疑似误用',
                    'context': f'示例: "{correct}" 误写为 "{context_matches[0]}"',
                })
    
    # —— 2e. 连续标点/空括号 ——
    bad_punct = re.findall(r'[，,]{2,}|[。.]{2,}|[、]{2,}', text)
    if bad_punct:
        issues.append({
            'dimension': '标点符号',
            'severity': 'P2',
            'message': f'发现 {len(bad_punct)} 处连续重复标点',
            'context': f'示例: {bad_punct[:3]}',
        })
    
    empty_brackets = re.findall(r'[（(]\s*[）)]', text)
    if empty_brackets:
        issues.append({
            'dimension': '内容缺失',
            'severity': 'P1',
            'message': f'发现 {len(empty_brackets)} 处空括号，可能遗漏内容',
            'context': '搜索"（）"或"()"',
        })
    
    # —— 2f. 数字合计校验（提取编号列表中的金额） ——
    numbered_items = re.findall(r'(?:[（(]?\d+[)）.．、]\s*[^。；\n]*?(\d+\.?\d*)\s*(?:万元|元|%))', text)
    if len(numbered_items) >= 2:
        issues.append({
            'dimension': '合计校验',
            'severity': 'P2',
            'message': f'发现 {len(numbered_items)} 个编号金额项，建议手动核实合计是否等于分项之和',
            'context': f'提取到的金额: {numbered_items[:5]}',
        })
    
    # —— 2g. 百分数合计 ——
    percents = re.findall(r'(\d+\.?\d*)%', text)
    if len(percents) >= 2:
        # 找连续的百分数
        pct_values = []
        for p in percents:
            try:
                pct_values.append(float(p))
            except:
                pass
        if len(pct_values) >= 2 and 95 < sum(pct_values[:min(10, len(pct_values))]) < 105:
            pass  # 接近100%可能是正常的结构占比
        elif len(pct_values) >= 3:
            issues.append({
                'dimension': '百分数合计',
                'severity': 'P2',
                'message': f'发现 {len(pct_values)} 处百分数，建议核实结构占比合计是否为100%',
                'context': f'检测到的百分数: {pct_values[:8]}',
            })
    
    # —— 2h. 法规引用格式 ——
    law_patterns = re.findall(r'(?:《[^》]+》)(?:\s*(?:第[一二三四五六七八九十\d]+[条章节]|\([^)]+\)))?', text)
    incomplete_citations = re.findall(r'《[^》]*$|(?<!\《)[^》]*》', text)
    if incomplete_citations:
        issues.append({
            'dimension': '法规引用',
            'severity': 'P1',
            'message': f'发现 {len(incomplete_citations)} 处书名号不完整，法规引用可能缺漏',
            'context': f'示例: {incomplete_citations[:3]}',
        })
    
    # —— 汇总 ——
    severity_count = defaultdict(int)
    for i in issues:
        severity_count[i['severity']] += 1
    
    print(f"  检出: {len(issues)} 个问题 (P0:{severity_count.get('P0',0)} P1:{severity_count.get('P1',0)} P2:{severity_count.get('P2',0)})")
    
    return {
        'issues': issues,
        'total': len(issues),
        'severity_count': dict(severity_count),
        'checks_performed': ['金额单位', '日期格式', '金额大写', '错别字', '标点符号', '空括号', '数字合计', '百分数', '法规引用'],
    }


# ============================================================
# Step 3: 深度复核（15维度AI框架）
# ============================================================
def step3_deep_review_framework(text: str, report_name: str = "") -> Dict:
    """生成15维度深度复核提示词框架
    
    本步骤生成结构化提示词，由 AI 执行。包含：
    - 10维正文复核 + 5维三方交叉
    - 6条误报抑制规则
    - 场景化校准
    """
    print("\n" + "─" * 50)
    print("  🎯 Step 3/4: 15维度深度复核框架")
    print("─" * 50)
    
    # 提取报告关键信息
    report_len = len(text)
    first_500 = text[:500]
    
    # 检测审计类型
    audit_type = "综合"
    type_patterns = {
        '经责审计': r'经济责任|离任|任中|自然资源',
        '收支审计': r'收支|财务收支',
        '预算执行': r'预算执行|部门预算|决算',
        '专项资金': r'专项资金|专款|补助资金',
        '往来款清理': r'往来款|应收|应付|暂存|暂付',
        '招投标': r'招标|投标|中标|采购',
        '国企审计': r'国有企业|国有资本|国资',
        '工程决算': r'工程|竣工|结算|造价',
        '绩效评价': r'绩效|绩效评价|绩效目标',
        '补贴审计': r'补贴|补助|惠农|耕地',
        '成本效益': r'成本效益|投入产出|效益分析',
        '能源审计': r'能源|节能|碳排放|碳中和',
    }
    for atype, pattern in type_patterns.items():
        if re.search(pattern, first_500):
            audit_type = atype
            break
    
    # 生成15维提示词
    dimensions = [
        {
            "id": "①",
            "name": "逻辑一致性",
            "focus": "检查报告全文是否存在前后矛盾、因果断裂、措辞不一致",
            "prompt": f"""请逐段阅读以下审计报告，检查逻辑一致性：
1. 同一事项在不同章节的描述是否一致（金额、定性、时间）
2. "问题→原因→结论→建议"的逻辑链是否完整无跳跃
3. 是否存在"发现问题A→却得出建议B"的错位
4. 报告中的"但是""然而"等转折是否前后逻辑自洽

=== 报告内容 ===
{text[:8000]}

请以表格输出：序号 | 位置 | 发现 | 严重程度(P0/P1/P2) | 修改建议""",
        },
        {
            "id": "②",
            "name": "问题定性精确度",
            "focus": "检查问题定性段落是否有模糊词、主观判断、数据不匹配",
            "prompt": f"""请审查以下审计报告中的问题定性表述：
1. 是否使用"部分""个别""有些"等模糊词且未跟具体数据
2. 定性词（违规/不规范/管理漏洞）是否与问题严重程度匹配
3. 是否有"性质严重""影响恶劣"等主观判断而无事实支撑
4. 金额/比例数据是否准确且与定性匹配

=== 报告内容 ===
{text[:8000]}

FP抑制规则：若"部分""个别"后跟具体数字 → 不标记
输出表格：序号 | 原文 | 问题 | 严重程度 | 修改建议""",
        },
        {
            "id": "③",
            "name": "整改建议靶向性",
            "focus": "检查整改建议是否有责任人、时限、验证标准",
            "prompt": f"""请审查以下审计报告中的整改建议：
1. 每条建议是否明确了责任主体（具体到部门/岗位）
2. 是否包含整改时限要求
3. 是否有可验证的整改标准（不是"加强管理"这种）
4. 整改措施是否与问题一一对应

=== 报告内容 ===
{text[:8000]}

输出表格：问题 | 原建议 | 缺失要素 | 改写建议""",
        },
        {
            "id": "④",
            "name": "证据链完整性",
            "focus": "检查结论性表述是否有证据支撑——'有结论无证据'",
        },
        {
            "id": "⑤",
            "name": "风险后果推演",
            "focus": "检查是否从财务/合规/经营三维度评估了问题的影响",
        },
        {
            "id": "⑥",
            "name": "审计目标覆盖度",
            "focus": "检查审计实施方案中的目标在报告中是否全部回应",
        },
        {
            "id": "⑦",
            "name": "管理建议书受众适配",
            "focus": "检查建议是建设性的还是挑刺式的",
        },
        {
            "id": "⑧",
            "name": "报告摘要可读性",
            "focus": "检查摘要是否独立承载了完整信息",
        },
        {
            "id": "⑨",
            "name": "跨项目口径一致性",
            "focus": "同类问题在不同报告中的定性/建议是否一致",
        },
        {
            "id": "⑩",
            "name": "措辞情绪化评估",
            "focus": "检查是否有主观情绪化表达，FP-1白名单过滤",
        },
        {
            "id": "⑪",
            "name": "报告↔附表数据一致性",
            "focus": "正文数据与附表数字是否一致",
        },
        {
            "id": "⑫",
            "name": "报告↔取证单证据对应",
            "focus": "结论是否有原始证据支撑",
        },
        {
            "id": "⑬",
            "name": "取证单↔附表数据溯源",
            "focus": "原始记录→汇总统计是否正确",
        },
        {
            "id": "⑭",
            "name": "取证单→报告完整闭环",
            "focus": "检查是否有取证单发现但报告未反映的问题（漏报）",
        },
        {
            "id": "⑮",
            "name": "全链路金额追踪",
            "focus": "原始→汇总→报告三个环节的金额是否一致",
        },
    ]
    
    # 各维度提示词（正文10维+交叉5维）
    dim_prompts_1_3 = [d for d in dimensions if d['id'] in '①②③']
    
    # 场景化FP规则参考
    fp_rules = {
        '经责审计': ['FP-1A: 标准定性词(失职/渎职/负有直接责任)不误标为情绪化', 'FP-1B: 审计评价中"基本能够"为公文标配，不标为模糊'],
        '预算执行': ['FP-3A: "基本完成"在预算语境下合法，不标为模糊', 'FP-3B: 超预算≠违规，需区分是否经审批调整'],
        '采购审计': ['FP-6A: 围标串标需多维度交叉确认，单一信号不直接定性'],
        '绩效评价': ['FP-11A~11D: 30条绩效专有白名单（效果不佳/指标不科学等为专业表述）'],
        '工程决算': ['FP-10A: "工程量"与"工程量清单"不互视为矛盾', 'FP-10B: 财务口径成本与工程造价口径的区别'],
    }
    
    framework = {
        'audit_type': audit_type,
        'report_name': report_name,
        'report_length': report_len,
        'dimensions': [],
        'fp_rules': fp_rules.get(audit_type, ['FP-G1~G6: 通用6条误报抑制']),
        'execution_notes': [
            '本框架生成15维提示词，由AI逐维执行',
            '执行规则：先10维正文（①②③…⑩），再5维交叉（⑪~⑮）',
            '每维输出格式统一：序号 | 位置 | 发现 | P0/P1/P2 | 修改建议',
            f'本报告类型为{audit_type}，应用相应场景FP规则',
            '置信度"低"的发现不进入主表，放入"仅供参考"附录',
            '金额差异<0.01%或<1000元标记为"可接受尾差"非P0',
        ],
    }
    
    for d in dimensions:
        dim_info = {
            'id': d['id'],
            'name': d['name'],
            'focus': d['focus'],
            'category': '正文' if d['id'] in '①②③④⑤⑥⑦⑧⑨⑩' else '交叉复核',
            'risk_level': '致命层' if d['id'] in '⑪⑫⑭⑮' else ('重要层' if d['id'] in '⑬' else '基础层'),
        }
        if 'prompt' in d:
            dim_info['ai_prompt'] = d['prompt']
        framework['dimensions'].append(dim_info)
    
    categories = defaultdict(int)
    for d in framework['dimensions']:
        categories[d['category']] += 1
    risk_levels = defaultdict(int)
    for d in framework['dimensions']:
        risk_levels[d['risk_level']] += 1
    
    print(f"  审计类型: {audit_type}")
    print(f"  维度框架: {categories['正文']}维正文 + {categories['交叉复核']}维交叉")
    print(f"  风险分布: 致命{risk_levels['致命层']} 重要{risk_levels['重要层']} 基础{risk_levels['基础层']}")
    print(f"  FP规则: {len(framework['fp_rules'])}条场景专属")
    
    return framework


# ============================================================
# Step 4: 自动告警 & 汇总
# ============================================================
def step4_alert_and_summary(step1_result: Dict, step2_result: Dict, 
                             step3_framework: Dict, report_name: str) -> Dict:
    """自动告警：汇总四步结果，分级输出"""
    print("\n" + "─" * 50)
    print("  🚨 Step 4/4: 告警汇总 & 分级输出")
    print("─" * 50)
    
    # 汇总所有问题
    all_issues = []
    
    # Step1 RAG知识
    rag_topics = step1_result.get('topics', [])
    rag_knowledge = step1_result.get('rag_knowledge', [])
    rag_services = step1_result.get('services_status', {})
    
    # Step2 快速复核问题
    quick_issues = step2_result.get('issues', [])
    all_issues.extend(quick_issues)
    
    # 按严重程度统计
    severity_map = {'P0': 0, 'P1': 0, 'P2': 0}
    for i in all_issues:
        sev = i.get('severity', 'P2')
        severity_map[sev] = severity_map.get(sev, 0) + 1
    
    # 生成知识缺口检测
    knowledge_gaps = []
    if rag_topics:
        for topic in rag_topics:
            topic_name = topic.get('name', '')
            # 检查是否有RAG结果覆盖
            matched = any(topic_name in str(r.get('topic', '')) for r in rag_knowledge if 'error' not in r)
            if not matched:
                knowledge_gaps.append(f"主题「{topic_name}」在知识库中匹配不足，建议补充相关资料")
    
    # 告警摘要
    alert_summary = {
        'report_name': report_name,
        'timestamp': datetime.now(TZ).isoformat(),
        'total_issues': len(all_issues),
        'severity_breakdown': severity_map,
        'audit_type': step3_framework.get('audit_type', '综合'),
        'rag_services_ok': rag_services.get('rag', False),
        'rag_topics_found': len(rag_topics),
        'rag_sources_matched': sum(len(r.get('sources', [])) for r in rag_knowledge if 'error' not in r),
        'knowledge_gaps': knowledge_gaps,
        'dimensions_covered': f"{step3_framework.get('dimensions', [])}",
        'fp_rules_applied': step3_framework.get('fp_rules', []),
    }
    
    # 告警级别判定
    if severity_map.get('P0', 0) > 0:
        alert_level = '🔴 紧急'
    elif severity_map.get('P1', 0) > 3:
        alert_level = '🟡 需要注意'
    else:
        alert_level = '🟢 正常'
    
    alert_summary['alert_level'] = alert_level
    
    print(f"  总问题数: {len(all_issues)}")
    print(f"  分级: P0={severity_map.get('P0',0)} P1={severity_map.get('P1',0)} P2={severity_map.get('P2',0)}")
    print(f"  知识缺口: {len(knowledge_gaps)} 个")
    print(f"  告警级别: {alert_level}")
    
    return alert_summary


# ============================================================
# 统一报告生成
# ============================================================
def generate_unified_report(step1: Dict, step2: Dict, step3: Dict, 
                            step4: Dict, report_name: str, deep: bool = False) -> str:
    """生成统一的四步串联复核报告"""
    
    lines = [
        f"# 📋 审计报告复核报告（四步串联 v1.0）",
        f"",
        f"| 项目 | 内容 |",
        f"|:-----|:-----|",
        f"| 报告名称 | {report_name} |",
        f"| 复核时间 | {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} |",
        f"| 复核深度 | {'深度复核 (15维)' if deep else '快速复核 (四步串联)'} |",
        f"| 审计类型 | {step3.get('audit_type', '综合')} |",
        f"| 服务状态 | RAG: {'✅' if step1.get('services_status',{}).get('rag') else '❌'} |",
        f"| 告警级别 | {step4.get('alert_level', 'N/A')} |",
        f"",
        f"---",
        f"",
    ]
    
    # ── Step 1: RAG增强 ──
    lines.append("## 📚 Step 1: RAG知识库增强")
    topics = step1.get('topics', [])
    if topics:
        lines.append(f"**识别审计主题**: {', '.join(t['name'] for t in topics[:6])}")
        lines.append("")
    
    rag_knowledge = step1.get('rag_knowledge', [])
    rag_ok = [r for r in rag_knowledge if 'error' not in r]
    if rag_ok:
        lines.append("**RAG知识匹配**:")
        for r in rag_ok[:4]:
            sources = r.get('sources', [])
            lines.append(f"- **{r['topic']}** (置信度 {r.get('confidence', 'N/A')})")
            for s in sources[:2]:
                lines.append(f"  - 📄 `{s}`")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # ── Step 2: 快速复核 ──
    lines.append("## 🔍 Step 2: 本地快速复核")
    quick_issues = step2.get('issues', [])
    if quick_issues:
        lines.append(f"**检出 {len(quick_issues)} 个问题**:")
        lines.append("")
        lines.append("| # | 检查维度 | 严重程度 | 问题 |")
        lines.append("|:--|:---------|:---------|:-----|")
        for i, issue in enumerate(quick_issues, 1):
            sev_icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}.get(issue['severity'], '•')
            lines.append(f"| {i} | {sev_icon} {issue['dimension']} | {issue['severity']} | {issue['message'][:80]} |")
        lines.append("")
    else:
        lines.append("✅ 未发现明显的格式/规范性低级错误")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # ── Step 3: 深度复核框架 ──
    lines.append("## 🎯 Step 3: 15维度深度复核框架")
    lines.append(f"**审计类型**: {step3.get('audit_type', '综合')}")
    lines.append(f"**维度覆盖**: {len(step3.get('dimensions', []))} 维度")
    lines.append("")
    lines.append("| 维度 | 类别 | 风险等级 | 检查重点 |")
    lines.append("|:-----|:-----|:---------|:---------|")
    for d in step3.get('dimensions', []):
        risk_icon = {'致命层': '🔴', '重要层': '🟡', '基础层': '🟢'}.get(d['risk_level'], '•')
        lines.append(f"| {d['id']} {d['name']} | {d['category']} | {risk_icon} {d['risk_level']} | {d['focus'][:50]} |")
    lines.append("")
    
    # FP规则
    fp_rules = step3.get('fp_rules', [])
    if fp_rules:
        lines.append("**应用FP规则**:")
        for rule in fp_rules:
            lines.append(f"- {rule}")
        lines.append("")
    
    execution_notes = step3.get('execution_notes', [])
    if execution_notes:
        lines.append("**AI执行说明**:")
        for note in execution_notes:
            lines.append(f"- {note}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # ── Step 4: 告警汇总 ──
    lines.append("## 🚨 Step 4: 告警汇总")
    
    severity = step4.get('severity_breakdown', {})
    lines.append(f"**告警级别**: {step4.get('alert_level', 'N/A')}")
    lines.append(f"**总问题数**: {step4.get('total_issues', 0)} (P0:{severity.get('P0',0)} P1:{severity.get('P1',0)} P2:{severity.get('P2',0)})")
    lines.append("")
    
    gaps = step4.get('knowledge_gaps', [])
    if gaps:
        lines.append("**⚠️ 知识缺口**:")
        for g in gaps:
            lines.append(f"- {g}")
        lines.append("")
    
    lines.append("**覆盖统计**:")
    lines.append(f"- RAG知识源匹配: {step4.get('rag_sources_matched', 0)} 个文件")
    lines.append(f"- 检查维度覆盖: {len(step3.get('dimensions', []))} 个维度")
    lines.append(f"- 应用FP规则: {len(step3.get('fp_rules', []))} 条")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # 建议操作
    lines.append("## 💡 后续操作建议")
    sev = step4.get('severity_breakdown', {})
    if sev.get('P0', 0) > 0:
        lines.append("1. 🔴 **紧急**: 逐项核实P0级问题，提交前必须修改")
    if sev.get('P1', 0) > 0:
        lines.append("2. 🟡 **重要**: P1级问题建议发回项目组修改")
    if deep:
        lines.append("3. 📋 运行15维AI深度复核（将报告全文提供给AI执行Step 3各维度提示词）")
    else:
        lines.append("3. 📋 如需15维深度复核，使用 `--deep` 参数或对Step 3执行AI审查")
    if gaps := step4.get('knowledge_gaps', []):
        lines.append(f"4. 📚 补充 {len(gaps)} 个知识缺口：向RAG知识库添加相关资料")
    lines.append("5. 🔄 修改后重新运行复核，确认问题已闭环")
    lines.append("")
    
    lines.append("---")
    lines.append("*由四步串联复核工作流自动生成 | report_review_workflow.py v1.0*")
    
    return '\n'.join(lines)


# ============================================================
# 主工作流
# ============================================================
def run_full_workflow(file_path: str = None, text: str = None, 
                      deep: bool = False, output_json: bool = False) -> Dict:
    """运行完整的四步串联复核"""
    
    report_name = Path(file_path).stem if file_path else "在线报告"
    
    print("\n" + "=" * 60)
    print(f"  审计报告四步串联复核 v1.0")
    print(f"  报告: {report_name}")
    print(f"  深度: {'深度复核' if deep else '标准复核'}")
    print("=" * 60)
    
    # 读取文本
    if file_path and not text:
        fp = Path(file_path)
        if not fp.exists():
            return {"error": f"文件不存在: {file_path}"}
        ext = fp.suffix.lower()
        if ext in ('.txt', '.md'):
            text = fp.read_text(encoding='utf-8')
        elif ext == '.docx':
            try:
                from docx import Document
                doc = Document(str(fp))
                text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            except ImportError:
                return {"error": "需要安装 python-docx: pip install python-docx"}
        else:
            try:
                text = fp.read_text(encoding='utf-8')
            except:
                return {"error": f"不支持的文件格式: {ext}"}
        print(f"  已读取: {len(text)} 字符")
    
    if not text:
        return {"error": "没有报告内容"}
    
    # ════ Step 1 ════
    step1 = step1_rag_enhanced(file_path=file_path, text=text)
    
    # ════ Step 2 ════
    step2 = step2_quick_review(text)
    
    # ════ Step 3 ════
    step3 = step3_deep_review_framework(text, report_name)
    
    # ════ Step 4 ════
    step4 = step4_alert_and_summary(step1, step2, step3, report_name)
    
    # ════ 生成统一报告 ════
    unified_report = generate_unified_report(step1, step2, step3, step4, report_name, deep)
    
    # 保存报告
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TZ).strftime('%Y%m%d_%H%M%S')
    safe_name = re.sub(r'[^\w]', '_', report_name)
    
    # Markdown
    md_path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(unified_report)
    
    # JSON
    json_path = OUTPUT_DIR / f"{safe_name}_{timestamp}.json"
    full_result = {
        'report_name': report_name,
        'timestamp': datetime.now(TZ).isoformat(),
        'deep': deep,
        'step1_rag': {k: v for k, v in step1.items() if k != 'review_advice'},
        'step2_quick': step2,
        'step3_deep_framework': step3,
        'step4_alert': step4,
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"  ✅ 四步串联复核完成")
    print(f"  📄 Markdown: {md_path}")
    print(f"  📊 JSON:     {json_path}")
    print(f"{'=' * 60}\n")
    
    result = {
        **full_result,
        'unified_report': unified_report,
        'md_path': str(md_path),
        'json_path': str(json_path),
    }
    
    if output_json:
        print(json.dumps({k: v for k, v in full_result.items() if k != 'unified_report'}, 
                        ensure_ascii=False, indent=2))
    
    return result


# ============================================================
# 目录监控模式（自动检测新报告）
# ============================================================
def load_watch_state() -> Dict:
    """加载监控状态"""
    if WATCH_STATE_FILE.exists():
        with open(WATCH_STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'seen_files': {}, 'last_scan': None}


def save_watch_state(state: Dict):
    """保存监控状态"""
    WATCH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCH_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def scan_reports_dir(watch_dir: str) -> List[str]:
    """扫描报告目录，发现新文件"""
    wp = Path(watch_dir)
    if not wp.exists():
        print(f"[监控] 目录不存在: {watch_dir}")
        return []
    
    report_exts = {'.docx', '.pdf', '.txt', '.md'}
    current_files = {}
    
    for fp in wp.rglob('*'):
        if fp.suffix.lower() in report_exts and fp.is_file():
            stat = fp.stat()
            current_files[str(fp)] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'hash': hashlib.md5(str(stat.st_mtime).encode()).hexdigest()[:8],
            }
    
    state = load_watch_state()
    seen = state.get('seen_files', {})
    
    new_files = []
    modified_files = []
    
    for fpath, info in current_files.items():
        if fpath not in seen:
            new_files.append(fpath)
        elif seen[fpath].get('hash') != info['hash']:
            modified_files.append(fpath)
    
    # 更新状态
    state['seen_files'] = current_files
    state['last_scan'] = datetime.now(TZ).isoformat()
    save_watch_state(state)
    
    changed = new_files + modified_files
    
    if changed:
        print(f"\n[监控] 检测到变化:")
        for f in new_files:
            print(f"  🆕 新增: {f}")
        for f in modified_files:
            print(f"  📝 修改: {f}")
    
    return changed


def watch_mode(watch_dir: str, deep: bool = False, interval: int = 60):
    """目录监控模式"""
    print(f"\n{'=' * 60}")
    print(f"  👁️  报告自动检测监控模式")
    print(f"  目录: {watch_dir}")
    print(f"  间隔: {interval}秒")
    print(f"  深度: {'深度复核' if deep else '标准复核'}")
    print(f"{'=' * 60}\n")
    
    print("首次扫描...")
    initial = scan_reports_dir(watch_dir)
    if initial:
        print(f"发现 {len(initial)} 个新文件，立即复核...")
        for f in initial[:3]:  # 首次最多处理3个
            try:
                run_full_workflow(file_path=f, deep=deep)
            except Exception as e:
                print(f"  ❌ 复核失败 ({Path(f).name}): {e}")
    else:
        print("无新文件，进入监控模式...")
    
    print(f"\n每{interval}秒扫描一次，按 Ctrl+C 停止...\n")
    
    try:
        while True:
            time.sleep(interval)
            changed = scan_reports_dir(watch_dir)
            if changed:
                for f in changed:
                    try:
                        print(f"\n🚨 自动触发复核: {Path(f).name}")
                        run_full_workflow(file_path=f, deep=deep)
                    except Exception as e:
                        print(f"  ❌ 复核失败: {e}")
    except KeyboardInterrupt:
        print("\n监控已停止")


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='审计报告四步串联复核工作流')
    parser.add_argument('--file', '-f', help='报告文件路径 (.docx/.pdf/.txt/.md)')
    parser.add_argument('--text', '-t', help='直接输入报告文本')
    parser.add_argument('--deep', action='store_true', help='深度复核模式（15维）')
    parser.add_argument('--json', action='store_true', help='JSON输出')
    parser.add_argument('--watch', '-w', help='目录监控模式，自动检测新报告')
    parser.add_argument('--interval', type=int, default=60, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    if args.watch:
        watch_mode(args.watch, deep=args.deep, interval=args.interval)
    elif args.file or args.text:
        run_full_workflow(
            file_path=args.file,
            text=args.text,
            deep=args.deep,
            output_json=args.json,
        )
    else:
        parser.print_help()

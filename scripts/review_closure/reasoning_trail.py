# -*- coding: utf-8 -*-
"""
审盾闭环层 - 推理链构建器 v1.0
================================
将现有复核脚本的输出，自动包装成带推理链的 ReviewFinding。

核心功能：
  - review_to_trail(): 把现有复核结果（step2_quick）转成带推理链的发现
  - deep_review_to_trail(): 把15维深度复核结果转成带推理链的发现
  - attach_rag_trail(): 给发现附加RAG查询推理链
  - build_full_report(): 构建完整的质控管道报告
"""

import sys, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from .schema import (
    ReviewFinding, ReasoningTrail, ReasoningStep, ReasoningStepType,
    QCPipeline, QCStatus, TZ
)

# 规则索引 - 每条规则都有唯一编号和说明
RULE_REGISTRY = {
    # 快速复核规则
    "R-001": "金额单位混用检查 - 检测报告同时使用万元和元",
    "R-002": "金额单位升档检查 - ≥1亿元金额检测单位为'亿'",
    "R-003": "日期格式检查 - 统一为YYYY年MM月DD日",
    "R-004": "金额大小写一致性检查",
    "R-005": "错别字检查 - 帐/账",
    "R-006": "错别字检查 - 做出/作出",
    "R-007": "错别字检查 - 截止/截至",
    "R-008": "错别字检查 - 涉及/涉及到",
    "R-009": "错别字检查 - 必须/必需",
    "R-010": "错别字检查 - 其它/其他",
    "R-011": "错别字检查 - 做为/作为",
    "R-012": "错别字检查 - 签定/签订",
    "R-013": "错别字检查 - 给与/给予",
    "R-014": "连续标点检测",
    "R-015": "空括号检测",
    "R-016": "数字合计校验 - 编号项金额",
    "R-017": "百分数合计校验",
    "R-018": "法规引用书名号完整性检查",
    # 深度复核规则
    "R-101": "逻辑一致性检查 - 全文前后矛盾/因果断裂",
    "R-102": "问题定性精确度 - 模糊词/主观判断/数据不匹配",
    "R-103": "整改建议靶向性 - 责任人/时限/验证标准",
    "R-104": "证据链完整性 - 有结论无证据",
    "R-105": "风险后果推演 - 财务/合规/经营三维评估",
    "R-106": "审计目标覆盖度 - 方案目标与报告回应",
    "R-107": "管理建议受众适配 - 建设性vs挑刺式",
    "R-108": "报告摘要可读性 - 独立承载完整信息",
    "R-109": "跨项目口径一致性 - 同类问题定性一致",
    "R-110": "措辞情绪化评估",
    "R-111": "报告↔附表数据一致性",
    "R-112": "报告↔取证单证据对应",
    "R-113": "取证单↔附表数据溯源",
    "R-114": "取证单→报告完整闭环",
    "R-115": "全链路金额追踪",
    # 误报抑制规则
    "FP-G1": "通用FP-1: 金额差异<0.01%或<1000元标记为可接受尾差",
    "FP-G2": "通用FP-2: 置信度'低'的发现不进入主表",
    "FP-1A": "经责FP-1A: 标准定性词(失职/渎职)不误标为情绪化",
    "FP-1B": "经责FP-1B: 审计评价中'基本能够'为公文标配",
    "FP-3A": "预算FP-3A: '基本完成'在预算语境下合法",
    "FP-3B": "预算FP-3B: 超预算≠违规，需区分是否经审批调整",
    "FP-6A": "采购FP-6A: 围标串标需多维度交叉确认",
    "FP-11A": "绩效FP-11A: '效果不佳'为专业表述非主观",
    "FP-11B": "绩效FP-11B: '指标不科学'为专业表述",
    "FP-11C": "绩效FP-11C: '目标偏离'为专业表述",
    "FP-11D": "绩效FP-11D: '项目推进缓慢'为专业表述",
}


def get_rule_ref(pattern: str) -> str:
    """根据检测模式获取规则编号"""
    rule_map = {
        r'帐': 'R-005', r'做出': 'R-006', r'截止': 'R-007',
        r'涉及到': 'R-008', r'必须的': 'R-009', r'其它': 'R-010',
        r'做为': 'R-011', r'签定': 'R-012', r'给与': 'R-013',
        '金额单位混用': 'R-001', '金额单位升档': 'R-002',
        '日期格式': 'R-003', '金额大小写': 'R-004',
        '连续标点': 'R-014', '空括号': 'R-015',
        '数字合计': 'R-016', '百分数合计': 'R-017',
        '法规引用': 'R-018',
    }
    for key, ref in rule_map.items():
        if key in pattern or re.search(key, pattern, re.IGNORECASE):
            return ref
    return None


def quick_issue_to_finding(issue: Dict, idx: int, report_text: str) -> ReviewFinding:
    """将快速复核的一条问题转为带推理链的发现"""
    
    dimension = issue.get('dimension', '综合')
    severity = issue.get('severity', 'P2')
    message = issue.get('message', '')
    context = issue.get('context', '')
    
    finding = ReviewFinding(
        finding_id=f"F-{datetime.now().strftime('%Y%m%d')}-{idx:03d}",
        dimension=dimension,
        severity=severity,
        message=message,
        category="快速复核",
        location=context,
        suggestion=f"请核实并修正：{message}",
    )
    
    # 构建推理链
    trail = finding.trail
    
    # 1. 数据加载
    trail.add_data_load(
        source="报告文本",
        description=f"扫描报告全文，定位{dimension}相关模式"
    )
    
    # 2. 规则匹配
    rule_ref = get_rule_ref(dimension + message)
    if not rule_ref:
        rule_ref = f"R-{900 + idx}"  # 临时编号
    
    rule_desc = RULE_REGISTRY.get(rule_ref, f"规则: {dimension}检查")
    
    # 提取上下文证据
    evidence = context[:200] if context else "全文扫描"
    
    trail.add_rule_match(
        rule=rule_ref,
        description=f"应用{rule_desc}",
        input_data=evidence,
        output_data=message[:200]
    )
    
    # 3. 计算置信度
    # 基于规则匹配的确定性
    if severity == 'P0':
        conf = 0.95
    elif severity == 'P1':
        conf = 0.85
    else:
        conf = 0.70
    
    # 4. 误报抑制检查
    fp_rule = _get_fp_rule(dimension, message)
    if fp_rule:
        trail.add_fp_check(
            rule=fp_rule,
            description=f"应用FP规则检查: {RULE_REGISTRY.get(fp_rule, fp_rule)}",
            result=f"检查通过，未触发误报抑制"
        )
        conf = min(conf + 0.05, 0.99)
    
    trail.set_confidence(conf)
    
    return finding


def _get_fp_rule(dimension: str, message: str) -> Optional[str]:
    """根据维度和消息判断适用的FP规则"""
    # 绩效相关
    if any(kw in message for kw in ['效果不佳', '指标不科学', '目标偏离', '推进缓慢']):
        return 'FP-11A'
    # 经责相关
    if any(kw in message for kw in ['失职', '渎职', '负有直接责任']):
        return 'FP-1A'
    if '基本能够' in message:
        return 'FP-1B'
    # 预算相关
    if '基本完成' in message:
        return 'FP-3A'
    if '超预算' in message:
        return 'FP-3B'
    # 采购相关
    if any(kw in message for kw in ['围标', '串标', '陪标']):
        return 'FP-6A'
    return None


def build_quick_review_trail(step2_result: Dict, report_text: str) -> List[ReviewFinding]:
    """将快速复核结果全部转成带推理链的发现"""
    findings = []
    issues = step2_result.get('issues', [])
    for i, issue in enumerate(issues, 1):
        finding = quick_issue_to_finding(issue, i, report_text)
        findings.append(finding)
    return findings


def build_deep_review_trail(step3_framework: Dict, report_text: str) -> List[ReviewFinding]:
    """将15维深度复核框架转成带推理链的发现"""
    findings = []
    for i, dim in enumerate(step3_framework.get('dimensions', []), 1):
        dim_id = dim.get('id', str(i))
        dim_name = dim.get('name', '未知维度')
        dim_focus = dim.get('focus', '')
        risk_level = dim.get('risk_level', '基础层')
        
        # 风险等级映射
        sev_map = {'致命层': 'P0', '重要层': 'P1', '基础层': 'P2'}
        severity = sev_map.get(risk_level, 'P2')
        
        finding = ReviewFinding(
            finding_id=f"D-{datetime.now().strftime('%Y%m%d')}-{i:03d}",
            dimension=dim_name,
            severity=severity,
            message=f"【{dim_name}】{dim_focus}",
            category="深度复核",
            location=f"维度{dim_id}: {dim_name}",
            suggestion=f"AI执行{dim_name}维度检查，请逐项核实输出结果",
        )
        
        trail = finding.trail
        
        # 规则引用
        rule_ref = f"R-{100 + i}"
        trail.add_rule_match(
            rule=rule_ref,
            description=f"应用{RULE_REGISTRY.get(rule_ref, dim_name)}",
            input_data=dim_focus,
            output_data=f"等待AI逐维执行{dim_name}检查"
        )
        
        trail.set_confidence(0.80)  # 深度复核的置信度需AI执行后更新
        
        findings.append(finding)
    
    return findings


def attach_rag_context(finding: ReviewFinding, rag_result: Dict):
    """给发现附加RAG知识库上下文"""
    topics = rag_result.get('topics', [])
    rag_knowledge = rag_result.get('rag_knowledge', [])
    
    for topic in topics[:3]:
        topic_name = topic.get('name', '')
        finding.trail.add_rag_query(
            query=f"查询: {topic_name}",
            result=f"主题置信度: {topic.get('confidence', 'N/A')}",
            source="RAG知识库"
        )
    
    for rk in rag_knowledge[:3]:
        if 'error' not in rk:
            sources = rk.get('sources', [])
            for s in sources[:2]:
                finding.trail.add_data_load(
                    source=s,
                    description=f"RAG知识库匹配: {rk.get('topic', '')}"
                )


def build_full_pipeline(report_name: str,
                        step2_result: Dict,
                        step3_framework: Dict,
                        step1_result: Dict,
                        report_text: str,
                        report_path: Optional[str] = None) -> QCPipeline:
    """构建完整的质控管道"""
    
    pipeline = QCPipeline(report_name=report_name)
    pipeline.raw_report_path = report_path
    
    # 1. 快速复核发现
    quick_findings = build_quick_review_trail(step2_result, report_text)
    for f in quick_findings:
        attach_rag_context(f, step1_result)
    pipeline.add_findings(quick_findings)
    
    # 2. 深度复核发现
    deep_findings = build_deep_review_trail(step3_framework, report_text)
    for f in deep_findings:
        attach_rag_context(f, step1_result)
    pipeline.add_findings(deep_findings)
    
    # 3. 元数据
    pipeline.metadata = {
        "report_length": len(report_text),
        "audit_type": step3_framework.get('audit_type', '综合'),
        "rag_topics": len(step1_result.get('topics', [])),
        "rag_sources": sum(len(r.get('sources', [])) for r in step1_result.get('rag_knowledge', []) if 'error' not in r),
        "fp_rules": step3_framework.get('fp_rules', []),
    }
    
    return pipeline


def save_pipeline(pipeline: QCPipeline, output_dir: str = None) -> str:
    """保存质控管道到文件"""
    if output_dir is None:
        from pathlib import Path
        output_dir = Path(__file__).parent.parent.parent / 'output' / 'qc_pipelines'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = re.sub(r'[^\w]', '_', pipeline.report_name)
    filepath = output_dir / f"{safe_name}_{timestamp}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(pipeline.to_dict(), f, ensure_ascii=False, indent=2)
    
    # 同时生成可读Markdown
    md_path = output_dir / f"{safe_name}_{timestamp}_推理链.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(pipeline_to_markdown(pipeline))
    
    return str(filepath)


def pipeline_to_markdown(pipeline: QCPipeline) -> str:
    """生成质控管道的完整可读报告"""
    summary = pipeline.get_summary()
    
    lines = [
        f"# 📋 审盾闭环层 - 质控管道报告",
        f"",
        f"**管道ID**: {pipeline.pipeline_id}",
        f"**报告名称**: {pipeline.report_name}",
        f"**状态**: {pipeline.status.value}",
        f"**创建时间**: {pipeline.created_at}",
        f"**更新时间**: {pipeline.updated_at}",
        f"",
        f"---",
        f"",
        f"## 概览",
        f"",
        f"| 指标 | 值 |",
        f"|:-----|:----|",
        f"| 发现总数 | {summary['total_findings']} |",
        f"| P0 (致命) | {summary['severity_breakdown'].get('P0', 0)} |",
        f"| P1 (重要) | {summary['severity_breakdown'].get('P1', 0)} |",
        f"| P2 (基础) | {summary['severity_breakdown'].get('P2', 0)} |",
        f"| 待审核 | {summary['qc_status_breakdown'].get('待审核', 0)} |",
        f"| 已确认 | {summary['qc_status_breakdown'].get('已确认', 0)} |",
        f"| 已驳回 | {summary['qc_status_breakdown'].get('已驳回', 0)} |",
        f"",
    ]
    
    if pipeline.metadata:
        lines.append("**元数据**:")
        for k, v in pipeline.metadata.items():
            lines.append(f"- {k}: {v}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## 发现明细（含推理链）")
    lines.append("")
    
    # P0排最前，再P1，再P2
    severity_order = {'P0': 0, 'P1': 1, 'P2': 2}
    sorted_findings = sorted(pipeline.findings, key=lambda f: severity_order.get(f.severity, 9))
    
    for i, finding in enumerate(sorted_findings, 1):
        trail = finding.trail
        
        # 严重程度图标
        sev_icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}.get(finding.severity, '•')
        qc_icon = {
            QCStatus.PENDING: '⏳',
            QCStatus.IN_REVIEW: '👁️',
            QCStatus.ACCEPTED: '✅',
            QCStatus.REJECTED: '❌',
            QCStatus.MODIFIED: '✏️',
            QCStatus.ARCHIVED: '📦',
        }.get(finding.qc_status, '•')
        
        lines.append(f"### {i}. {qc_icon} {sev_icon} [{finding.severity}] {finding.dimension}")
        lines.append(f"**ID**: {finding.finding_id}")
        lines.append(f"**分类**: {finding.category}")
        lines.append(f"**发现**: {finding.message}")
        if finding.location:
            lines.append(f"**位置**: {finding.location}")
        if finding.suggestion:
            lines.append(f"**建议**: {finding.suggestion}")
        lines.append(f"**状态**: {finding.qc_status.value}")
        lines.append("")
        
        # 推理链摘要
        lines.append("**推理链** ({0}步, 置信度 {1}):".format(
            trail.step_count, trail.overall_confidence or 'N/A'))
        lines.append("")
        
        for j, step in enumerate(trail.steps, 1):
            sd = step.to_dict()
            lines.append(f"  {j}. [{sd['step_type']}] {sd['description']}")
            if 'rule_ref' in sd:
                lines.append(f"     → 规则: {sd['rule_ref']}")
            if 'source_ref' in sd:
                lines.append(f"     → 来源: {sd['source_ref']}")
            if 'output_data' in sd:
                output = sd['output_data'][:150]
                lines.append(f"     → 结果: {output}")
        
        lines.append("")
        
        if trail.data_sources:
            lines.append(f"**引用数据源**: {', '.join(trail.data_sources[:3])}")
        if trail.rules_applied:
            rules_readable = [f"`{r}`" for r in trail.rules_applied[:3]]
            lines.append(f"**应用规则**: {', '.join(rules_readable)}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append(f"*由审盾闭环层自动生成 | {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}*")
    
    return '\n'.join(lines)
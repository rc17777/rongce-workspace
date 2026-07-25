# -*- coding: utf-8 -*-
"""
审盾闭环层 - CLI审核工具 v1.0
===============================
质控人员命令行界面。

用法：
  python -m scripts.review_closure.cli --help
  
  # 提交报告到质控管道
  python -m scripts.review_closure.cli submit --file 报告.docx
  
  # 查看队列
  python -m scripts.review_closure.cli list
  python -m scripts.review_closure.cli list --status 待审核
  
  # 查看看板
  python -m scripts.review_closure.cli dashboard
  
  # 查看管道详情
  python -m scripts.review_closure.cli show QC-20260721-143056-abc123
  
  # 查看推理链（推演过程）
  python -m scripts.review_closure.cli trail QC-20260721-143056-abc123 F-20260721-001
  
  # 审核单条发现
  python -m scripts.review_closure.cli review QC-20260721-143056-abc123 F-20260721-001 accept --reviewer 张三 --comment "确认发现，金额已核实"
  
  # 批量审核所有P0
  python -m scripts.review_closure.cli batch QC-20260721-143056-abc123 accept --severity P0 --reviewer 张三
  
  # 导出管道报告
  python -m scripts.review_closure.cli export QC-20260721-143056-abc123 --format md
  python -m scripts.review_closure.cli export QC-20260721-143056-abc123 --format json
"""

import sys, json, argparse, textwrap
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# 确保能导入同目录模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.review_closure.schema import (
    ReviewFinding, QCPipeline, QCStatus, TZ
)
from scripts.review_closure.reasoning_trail import (
    build_full_pipeline, save_pipeline, pipeline_to_markdown, RULE_REGISTRY
)
from scripts.review_closure.qc_pipeline import (
    submit_to_qc, list_queue, get_pipeline, review_finding,
    batch_review, get_qc_dashboard, get_qc_dashboard_markdown,
    _save_pipeline, QUEUE_DIR, ARCHIVE_DIR, REPORT_DIR
)


# ============================================================
# 命令行入口
# ============================================================

def cmd_submit(args):
    """提交报告到质控管道"""
    file_path = args.file
    text = args.text
    
    if not file_path and not text:
        print("❌ 请指定 --file 或 --text")
        return 1
    
    # 读取报告
    report_text = ""
    report_name = ""
    
    if file_path:
        fp = Path(file_path)
        if not fp.exists():
            print(f"❌ 文件不存在: {file_path}")
            return 1
        report_name = fp.stem
        try:
            report_text = fp.read_text(encoding='utf-8')
        except:
            # 尝试其他编码
            try:
                report_text = fp.read_text(encoding='gbk')
            except:
                print(f"❌ 无法读取文件: {file_path}")
                return 1
    elif text:
        report_name = args.name or "在线报告"
        report_text = text
    
    print(f"📄 报告: {report_name} ({len(report_text)} 字符)")
    
    # 模拟运行复核（简化版 - 使用内置规则快速检查）
    from scripts.review_closure.reasoning_trail import build_quick_review_trail, build_deep_review_trail
    
    # 快速复核
    step2_result = _run_quick_review(report_text)
    step3_framework = _build_framework(report_text, report_name)
    step1_result = {"topics": [], "rag_knowledge": [], "services_status": {"rag": False}}
    
    # 构建管道
    pipeline = build_full_pipeline(
        report_name=report_name,
        step2_result=step2_result,
        step3_framework=step3_framework,
        step1_result=step1_result,
        report_text=report_text,
        report_path=file_path,
    )
    
    # 提交到质控队列
    path = submit_to_qc(pipeline)
    
    summary = pipeline.get_summary()
    print(f"✅ 已提交到质控队列")
    print(f"   管道ID: {pipeline.pipeline_id}")
    print(f"   发现总数: {summary['total_findings']}")
    print(f"   P0: {summary['severity_breakdown'].get('P0', 0)}")
    print(f"   P1: {summary['severity_breakdown'].get('P1', 0)}")
    print(f"   P2: {summary['severity_breakdown'].get('P2', 0)}")
    print(f"   文件: {path}")
    print(f"   推理链报告: {REPORT_DIR / pipeline.pipeline_id}_推理链.md")
    print(f"")
    print(f"   > 使用以下命令查看详情:")
    print(f"   > python -m scripts.review_closure.cli show {pipeline.pipeline_id}")
    print(f"   > python -m scripts.review_closure.cli trail {pipeline.pipeline_id}")
    print(f"   > python -m scripts.review_closure.cli review {pipeline.pipeline_id} <finding_id> accept")
    
    return 0


def _run_quick_review(text: str) -> Dict:
    """内置快速复核（兼容report_review_workflow的输出格式）"""
    import re
    from collections import defaultdict
    
    issues = []
    
    # 金额单位混用
    has_wan = bool(re.search(r'\d+\.?\d*\s*万', text))
    has_yuan = bool(re.search(r'(?<!万)(?<!亿)\d{4,}\s*元', text))
    if has_wan and has_yuan:
        issues.append({
            'dimension': '金额单位', 'severity': 'P1',
            'message': '报告同时使用"万元"和"元"为单位，建议统一',
            'context': '检查全文金额单位是否一致',
        })
    
    # 错别字
    typo_rules = [
        (r'帐(?![篷蚊])', '账', '账务/账户/台账应为"账"'),
        (r'做出(?!了)', '作出', '公文规范用"作出决定/作出处理"'),
        (r'截止(?!到)', '截至', '"截止"不接宾语，"截至"可接宾语'),
        (r'涉及到', '涉及', '"涉及"已含"到"义'),
        (r'来自于', '来自', '"来自"已含"于"义'),
        (r'其它', '其他', '公文规范用"其他"而非"其它"'),
        (r'做为', '作为', '"作为"是规范写法'),
        (r'签定', '签订', '"签订合同"非"签定"'),
        (r'给与', '给予', '"给予"是规范写法'),
    ]
    for pattern, correct, explanation in typo_rules:
        matches = re.findall(pattern, text)
        if matches:
            issues.append({
                'dimension': '错别字', 'severity': 'P1' if len(matches) > 3 else 'P2',
                'message': f'{explanation} — 发现 {len(matches)} 处疑似误用',
                'context': f'示例: "{correct}" 误写为 "{matches[0]}"',
            })
    
    # 空括号
    empty_brackets = re.findall(r'[（(]\s*[）)]', text)
    if empty_brackets:
        issues.append({
            'dimension': '内容缺失', 'severity': 'P1',
            'message': f'发现 {len(empty_brackets)} 处空括号，可能遗漏内容',
            'context': '搜索"（）"或"()"',
        })
    
    # 法规引用书名号不完整
    incomplete = re.findall(r'《[^》]*$|(?<!\《)[^》]*》', text)
    if incomplete:
        issues.append({
            'dimension': '法规引用', 'severity': 'P1',
            'message': f'发现 {len(incomplete)} 处书名号不完整',
            'context': f'示例: {incomplete[:3]}',
        })
    
    # 日期格式
    dates = re.findall(r'\d{4}[年.\-/]\d{1,2}[月.\-/]\d{1,2}', text)
    bad_dates = [d for d in dates if not re.match(r'\d{4}年\d{1,2}月\d{1,2}日', d)]
    if bad_dates:
        issues.append({
            'dimension': '日期格式', 'severity': 'P2',
            'message': f'发现 {len(bad_dates)} 处非标准日期格式',
            'context': f'示例: {bad_dates[:3]}',
        })
    
    severity_count = defaultdict(int)
    for i in issues:
        severity_count[i['severity']] += 1
    
    return {
        'issues': issues,
        'total': len(issues),
        'severity_count': dict(severity_count),
        'checks_performed': ['金额单位', '错别字', '空括号', '法规引用', '日期格式'],
    }


def _build_framework(text: str, report_name: str) -> Dict:
    """内置框架生成"""
    import re
    audit_type = "综合"
    type_patterns = {
        '经责审计': r'经济责任|离任|任中',
        '专项资金': r'专项资金|专款|补助',
        '绩效评价': r'绩效|绩效评价|绩效目标',
        '预算执行': r'预算执行|部门预算|决算',
        '招投标': r'招标|投标|中标|采购',
        '工程决算': r'工程|竣工|结算|造价',
        '补贴审计': r'补贴|补助|惠农',
    }
    first_500 = text[:500]
    for atype, pattern in type_patterns.items():
        if re.search(pattern, first_500):
            audit_type = atype
            break
    
    dimensions = [
        {"id": "①", "name": "逻辑一致性", "focus": "全文前后矛盾、因果断裂", "risk_level": "重要层"},
        {"id": "②", "name": "问题定性精确度", "focus": "模糊词/主观判断", "risk_level": "重要层"},
        {"id": "③", "name": "整改建议靶向性", "focus": "责任人/时限/验证标准", "risk_level": "重要层"},
        {"id": "④", "name": "证据链完整性", "focus": "有结论无证据", "risk_level": "重要层"},
        {"id": "⑤", "name": "风险后果推演", "focus": "财务/合规/经营三维评估", "risk_level": "基础层"},
        {"id": "⑥", "name": "审计目标覆盖度", "focus": "方案目标与报告回应", "risk_level": "基础层"},
        {"id": "⑦", "name": "管理建议受众适配", "focus": "建设性vs挑刺式", "risk_level": "基础层"},
        {"id": "⑧", "name": "报告摘要可读性", "focus": "独立承载完整信息", "risk_level": "基础层"},
        {"id": "⑨", "name": "跨项目口径一致性", "focus": "同类问题定性一致", "risk_level": "基础层"},
        {"id": "⑩", "name": "措辞情绪化评估", "focus": "主观情绪化表达", "risk_level": "基础层"},
        {"id": "⑪", "name": "报告↔附表数据一致性", "focus": "正文数据与附表数字一致", "risk_level": "致命层"},
        {"id": "⑫", "name": "报告↔取证单证据对应", "focus": "结论是否有原始证据", "risk_level": "致命层"},
        {"id": "⑬", "name": "取证单↔附表数据溯源", "focus": "原始记录→汇总统计", "risk_level": "重要层"},
        {"id": "⑭", "name": "取证单→报告完整闭环", "focus": "取证单发现但报告未反映", "risk_level": "致命层"},
        {"id": "⑮", "name": "全链路金额追踪", "focus": "原始→汇总→报告金额一致", "risk_level": "致命层"},
    ]
    
    return {
        'audit_type': audit_type,
        'report_name': report_name,
        'report_length': len(text),
        'dimensions': dimensions,
        'fp_rules': ['FP-G1: 金额差异<0.01%或<1000元为可接受尾差'],
    }


def cmd_list(args):
    """列出质控队列"""
    items = list_queue(status_filter=args.status)
    
    if not items:
        print("✅ 队列为空，无待审核项")
        return 0
    
    print(f"📋 质控队列 ({len(items)} 项)")
    print("")
    print(f"{'管道ID':<30} {'报告名称':<25} {'发现数':<8} {'待审核':<8} {'状态':<10} {'创建时间':<16}")
    print("-" * 100)
    
    for item in items:
        pid = item.get('pipeline_id', '')
        name = item.get('report_name', '')[:22]
        total = len(item.get('findings', []))
        pending = sum(1 for f in item.get('findings', []) 
                      if f.get('qc_status') in ['待审核', '审核中'])
        status = item.get('status', '')
        created = item.get('created_at', '')[:16]
        
        sev_icon = '🚨' if any(f.get('severity') == 'P0' for f in item.get('findings', [])) else '📄'
        print(f"{sev_icon} {pid:<28} {name:<25} {total:<8} {pending:<8} {status:<10} {created:<16}")
    
    print("")
    print("使用 python -m scripts.review_closure.cli show <pipeline_id> 查看详情")
    print("使用 python -m scripts.review_closure.cli trail <pipeline_id> 查看推理链")
    
    return 0


def cmd_show(args):
    """显示管道详情"""
    pipeline = get_pipeline(args.pipeline_id)
    if not pipeline:
        print(f"❌ 管道不存在: {args.pipeline_id}")
        return 1
    
    summary = pipeline.get_summary()
    
    print(f"📋 管道详情: {pipeline.pipeline_id}")
    print(f"   报告: {pipeline.report_name}")
    print(f"   状态: {pipeline.status.value}")
    print(f"   创建: {pipeline.created_at[:19]}")
    print(f"   更新: {pipeline.updated_at[:19]}")
    if pipeline.completed_at:
        print(f"   完成: {pipeline.completed_at[:19]}")
    print("")
    
    print(f"   发现总数: {summary['total_findings']}")
    print(f"   🔴 P0: {summary['severity_breakdown'].get('P0', 0)}")
    print(f"   🟡 P1: {summary['severity_breakdown'].get('P1', 0)}")
    print(f"   🟢 P2: {summary['severity_breakdown'].get('P2', 0)}")
    print("")
    
    print(f"   质控状态:")
    for status, count in sorted(summary['qc_status_breakdown'].items()):
        print(f"     {status}: {count}")
    print("")
    
    print(f"   发现列表:")
    severity_order = {'P0': 0, 'P1': 1, 'P2': 2}
    sorted_findings = sorted(pipeline.findings, 
                             key=lambda f: (severity_order.get(f.severity, 9), f.finding_id))
    
    for i, f in enumerate(sorted_findings, 1):
        qc_icon = {
            QCStatus.PENDING: '⏳', QCStatus.IN_REVIEW: '👁️',
            QCStatus.ACCEPTED: '✅', QCStatus.REJECTED: '❌',
            QCStatus.MODIFIED: '✏️', QCStatus.ARCHIVED: '📦',
        }.get(f.qc_status, '•')
        sev_icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}.get(f.severity, '•')
        msg = f.message[:60]
        trail_steps = f.trail.step_count
        conf = f.trail.overall_confidence or 'N/A'
        
        print(f"   {i:2d}. {qc_icon} {sev_icon} [{f.severity}] {f.finding_id}")
        print(f"       {f.dimension}: {msg}")
        print(f"       推理链: {trail_steps}步 | 置信度: {conf} | 状态: {f.qc_status.value}")
        if f.qc_comment:
            print(f"       审核意见: {f.qc_comment}")
        print("")
    
    print(f"   操作提示:")
    print(f"   > python -m scripts.review_closure.cli trail {pipeline.pipeline_id} <finding_id>  查看推理链")
    print(f"   > python -m scripts.review_closure.cli review {pipeline.pipeline_id} <finding_id> accept  确认发现")
    print(f"   > python -m scripts.review_closure.cli review {pipeline.pipeline_id} <finding_id> reject  驳回发现")
    
    return 0


def cmd_trail(args):
    """显示推理链"""
    pipeline = get_pipeline(args.pipeline_id)
    if not pipeline:
        print(f"❌ 管道不存在: {args.pipeline_id}")
        return 1
    
    finding_id = args.finding_id
    
    if finding_id:
        # 显示单条推理链
        target = None
        for f in pipeline.findings:
            if f.finding_id == finding_id:
                target = f
                break
        
        if not target:
            print(f"❌ 发现不存在: {finding_id}")
            return 1
        
        print(f"🔍 推理链: {finding_id}")
        print(f"   维度: {target.dimension}")
        print(f"   严重程度: {target.severity}")
        print(f"   发现: {target.message}")
        print(f"   置信度: {target.trail.overall_confidence or 'N/A'}")
        print(f"   步骤数: {target.trail.step_count}")
        print("")
        print("=" * 60)
        
        for i, step in enumerate(target.trail.steps, 1):
            sd = step.to_dict()
            print(f"")
            print(f"  ▶ 步骤 {i}: [{sd['step_type']}]")
            print(f"    描述: {sd['description']}")
            if 'input_data' in sd:
                print(f"    输入: {sd['input_data'][:300]}")
            if 'output_data' in sd:
                print(f"    输出: {sd['output_data'][:300]}")
            if 'rule_ref' in sd:
                rule_desc = RULE_REGISTRY.get(sd['rule_ref'], '')
                print(f"    规则: {sd['rule_ref']} - {rule_desc}")
            if 'source_ref' in sd:
                print(f"    来源: {sd['source_ref']}")
            if 'confidence' in sd:
                print(f"    置信度: {sd['confidence']}")
        
        print("")
        print("=" * 60)
        
        if target.trail.data_sources:
            print(f"\n📄 引用数据源:")
            for s in target.trail.data_sources:
                print(f"  - {s}")
        
        if target.trail.rag_references:
            print(f"\n📚 RAG知识库引用:")
            for r in target.trail.rag_references[:5]:
                print(f"  - {r}")
        
        if target.trail.fp_checks:
            print(f"\n✅ 误报抑制检查:")
            for f in target.trail.fp_checks:
                print(f"  - {f}")
    else:
        # 显示所有推理链摘要
        print(f"🔍 推理链摘要: {pipeline.pipeline_id}")
        print("")
        for f in pipeline.findings:
            steps = f.trail.step_count
            conf = f.trail.overall_confidence or 'N/A'
            print(f"  [{f.severity}] {f.finding_id} ({f.dimension})")
            print(f"    步骤: {steps}步 | 置信度: {conf}")
            print(f"    数据源: {len(f.trail.data_sources)}个 | 规则: {len(f.trail.rules_applied)}条")
            print("")
        
        print(f"使用 python -m scripts.review_closure.cli trail {pipeline.pipeline_id} <finding_id> 查看完整推理链")
    
    return 0


def cmd_review(args):
    """审核单条发现"""
    success, msg = review_finding(
        pipeline_id=args.pipeline_id,
        finding_id=args.finding_id,
        action=args.action,
        reviewer=args.reviewer,
        comment=args.comment,
    )
    
    if success:
        print(f"✅ {msg}")
        return 0
    else:
        print(f"❌ {msg}")
        return 1


def cmd_batch(args):
    """批量审核"""
    results = batch_review(
        pipeline_id=args.pipeline_id,
        action=args.action,
        severity_filter=args.severity,
        reviewer=args.reviewer,
        comment=args.comment,
    )
    
    if results:
        print(f"✅ 批量审核完成 ({len(results)} 条)")
        for r in results:
            print(f"  {r}")
    else:
        print("没有符合条件的待审核发现")
    
    return 0


def cmd_dashboard(args):
    """显示质控看板"""
    if args.json:
        dash = get_qc_dashboard()
        print(json.dumps(dash, ensure_ascii=False, indent=2))
    else:
        md = get_qc_dashboard_markdown()
        print(md)
    
    return 0


def cmd_export(args):
    """导出管道报告"""
    pipeline = get_pipeline(args.pipeline_id)
    if not pipeline:
        print(f"❌ 管道不存在: {args.pipeline_id}")
        return 1
    
    fmt = args.format
    out_dir = args.outdir or REPORT_DIR
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    if fmt == 'md':
        md = pipeline_to_markdown(pipeline)
        path = Path(out_dir) / f"{pipeline.pipeline_id}_报告.md"
        path.write_text(md, encoding='utf-8')
        print(f"✅ 已导出Markdown报告: {path}")
    elif fmt == 'json':
        data = pipeline.to_dict()
        path = Path(out_dir) / f"{pipeline.pipeline_id}_报告.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已导出JSON报告: {path}")
    
    return 0


def cmd_help(args):
    """显示帮助"""
    parser.print_help()
    print("")
    print("可用子命令:")
    for cmd_name, (func, desc) in COMMANDS.items():
        print(f"  {cmd_name:<12} {desc}")
    return 0


# ============================================================
# 主入口
# ============================================================

COMMANDS = {
    'submit': (cmd_submit, '提交报告到质控管道'),
    'list': (cmd_list, '列出质控队列'),
    'show': (cmd_show, '显示管道详情'),
    'trail': (cmd_trail, '查看推理链（推演过程）'),
    'review': (cmd_review, '审核单条发现'),
    'batch': (cmd_batch, '批量审核发现'),
    'dashboard': (cmd_dashboard, '显示质控看板'),
    'export': (cmd_export, '导出管道报告'),
    'help': (cmd_help, '显示帮助'),
}

def build_parser():
    parser = argparse.ArgumentParser(
        description='审盾闭环层 - 质控审核CLI工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例:
              # 提交报告
              python -m scripts.review_closure.cli submit --file 报告.docx
              
              # 查看队列
              python -m scripts.review_closure.cli list
              
              # 审核发现
              python -m scripts.review_closure.cli review QC-20260721-123456-abc F-20260721-001 accept
              
              # 查看推理链
              python -m scripts.review_closure.cli trail QC-20260721-123456-abc F-20260721-001
        """),
    )
    parser.add_argument('command', nargs='?', help='子命令')

    parser.add_argument('--file', '-f', help='报告文件路径')
    parser.add_argument('--text', '-t', help='直接输入报告文本')
    parser.add_argument('--name', '-n', help='报告名称（--text时使用）')
    parser.add_argument('--status', '-s', help='按状态筛选')
    parser.add_argument('--pipeline_id', help='管道ID')
    parser.add_argument('--finding_id', help='发现ID')
    parser.add_argument('--action', choices=['accept', 'reject', 'modify', 'skip'], help='审核操作')
    parser.add_argument('--reviewer', '-r', default='质控人员', help='审核人')
    parser.add_argument('--comment', '-c', default='', help='审核意见')
    parser.add_argument('--severity', choices=['P0', 'P1', 'P2'], help='按严重程度筛选')
    parser.add_argument('--format', choices=['md', 'json'], default='md', help='导出格式')
    parser.add_argument('--outdir', '-o', help='导出目录')
    parser.add_argument('--json', '-j', action='store_true', help='JSON输出')
    return parser


parser = build_parser()


def main():
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    cmd = args.command
    if cmd not in COMMANDS:
        print(f"❌ 未知命令: {cmd}")
        print(f"可用命令: {', '.join(COMMANDS.keys())}")
        return 1
    
    func, _ = COMMANDS[cmd]
    return func(args)


if __name__ == '__main__':
    sys.exit(main())
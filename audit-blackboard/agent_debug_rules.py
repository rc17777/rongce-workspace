# -*- coding: utf-8 -*-
"""
融策Agent调试工具箱 v1.0 — Agent Debug Toolkit
================================================
灵感来源：AgentDebugX 论文（UIUC/Stanford/Google/UofT, 2026）

三模块：
  1. agent_debug_rules.py   — 确定性规则检测引擎（Detect）
  2. agent_deep_debug.py    — DeepDebug交接点定位（Attribute）
  3. agent_error_hub.py     — Error Hub错误共享库（积累 → 复用）

用法：
  # 规则检测
  python agent_debug_rules.py --project "XX项目" --agent "contract_hound"
  # 深度归因
  python agent_deep_debug.py --project "XX项目" --mode deepdebug
  # 错误库管理
  python agent_error_hub.py --project "XX项目" --action store
  python agent_error_hub.py --project "XX项目" --action query --pattern "handover_loss"
"""

import os, sys, json, re, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
DEBUG_DIR = BLACKBOARD / 'debug'
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════
# PART 1: 确定性规则检测引擎
# ═══════════════════════════════════════════

class AgentDebugRules:
    """
    不调LLM，纯规则检测Agent输出的机械性错误。
    对标 AgentDebugX 的 Detect 阶段。
    """

    # === 规则包1: 格式与协议错误 ===
    FORMAT_RULES = {
        'R001_empty_finding': {
            'desc': '发现记录缺少必填字段',
            'severity': 'P0',
            'required_fields': ['id', 'title', 'description', 'severity', 'source'],
        },
        'R002_amount_unit': {
            'desc': '金额单位不一致（元/万元混用）',
            'severity': 'P1',
            'pattern': r'(?:[1-9]\d{4,})\s*元(?!/\w)',
            'warning_threshold': 3,
        },
        'R003_date_format': {
            'desc': '日期格式不标准',
            'severity': 'P2',
            'pattern': r'\d{4}[/.]\d{1,2}[/.]\d{1,2}',
        },
        'R004_missing_finding_id': {
            'desc': '发现记录缺少ID',
            'severity': 'P0',
        },
        'R005_duplicate_finding_id': {
            'desc': '发现记录ID重复',
            'severity': 'P1',
        },
        'R006_invalid_severity': {
            'desc': '严重程度不在[P0,P1,P2,OBS]范围内',
            'severity': 'P1',
        },
    }

    # === 规则包2: 逻辑与一致性错误 ===
    LOGIC_RULES = {
        'R101_self_contradiction': {
            'desc': '同一Agent输出中包含自相矛盾的结论',
            'severity': 'P0',
            'keywords_positive': ['合规', '正常', '无异常', '通过', '符合规定'],
            'keywords_negative': ['违规', '异常', '问题', '不符合', '超标', '虚列'],
        },
        'R102_amount_mismatch': {
            'desc': '总计数与明细合计不符',
            'severity': 'P0',
        },
        'R103_conclusion_without_evidence': {
            'desc': '结论缺少支撑证据引用',
            'severity': 'P2',
            'conclusion_keywords': ['综上', '因此', '认定', '判断', '结论'],
            'evidence_gap': 200,  # 结论前后200字符内没引用证据
        },
        'R104_premature_success': {
            'desc': '过早声明任务完成（对标AgentDebugX）',
            'severity': 'P0',
            'success_markers': [
                r'任务.*完成', r'分析.*完成', r'检查.*通过',
                r'all.*pass', r'全部.*正常', r'未发现.*异常',
            ],
        },
        'R105_non_progress_loop': {
            'desc': '无进展循环（Agent重复输出相似内容）',
            'severity': 'P1',
            'similarity_threshold': 0.85,
            'min_repetitions': 3,
        },
    }

    # === 规则包3: 审计专项规则 ===
    AUDIT_RULES = {
        'R201_severity_inflation': {
            'desc': '严重程度虚高（小问题标P0）',
            'severity': 'P2',
            'low_impact_keywords': ['格式', '笔误', '错别字', '标点', '排版'],
            'inflated_severity': ['P0', 'P1'],
        },
        'R202_regulation_no_format': {
            'desc': '法规引用格式不规范',
            'severity': 'P2',
            'valid_patterns': [
                r'《.+?》',
                r'财预\[\d{4}\]\d+号',
                r'第\s*\d+\s*条',
                r'(\d{4})\s*年第\s*\d+\s*号',
            ],
        },
        'R203_amount_range_check': {
            'desc': '金额超出合理范围',
            'severity': 'P1',
            'reasonable_max': 1_000_000_000_000,  # 1万亿
        },
        'R204_missing_audit_trail': {
            'desc': '审计发现缺少取证来源标注',
            'severity': 'P1',
            'required_sources': ['凭证号', '合同编号', '发票号', '银行流水号', '审批单号'],
        },
        'R205_finding_no_recommendation': {
            'desc': '审计发现缺少整改建议',
            'severity': 'P2',
        },
    }

    # === 规则包4: 多Agent交接异常 ===
    HANDOVER_RULES = {
        'R301_handover_info_loss': {
            'desc': '交接包关键信息丢失',
            'severity': 'P0',
            'required_handover_fields': ['goal', 'confirmed_facts', 'findings_summary'],
        },
        'R302_finding_dropped': {
            'desc': '前任Agent发现被后续Agent遗漏',
            'severity': 'P0',
        },
        'R303_warning_ignored': {
            'desc': '前任Agent告警未被后续Agent响应',
            'severity': 'P1',
        },
        'R304_context_mismatch': {
            'desc': '交接上下文与新Agent任务不匹配',
            'severity': 'P2',
        },
        'R305_chain_break': {
            'desc': '交接链断裂（缺少中间Agent的handover）',
            'severity': 'P0',
        },
    }

    def __init__(self, project_slug, agent_name=None):
        self.project_slug = project_slug
        self.agent_name = agent_name
        self.project_dir = PROJECTS / project_slug
        self.findings_dir = self.project_dir / 'findings'
        self.handover_dir = self.project_dir / 'handovers'
        self.issues = []
        self.stats = {'total_checks': 0, 'issues_found': 0, 'by_severity': defaultdict(int)}

    def run_all(self):
        """运行全部规则检测。"""
        print(f"\n{'='*60}")
        print(f"🔍 Agent确定性规则检测 — {self.project_slug}")
        print(f"   目标Agent: {self.agent_name or '全部'}")
        print(f"{'='*60}\n")

        self._check_format()
        self._check_logic()
        self._check_audit()
        self._check_handover()

        # 汇总
        print(f"\n{'─'*60}")
        print(f"检测完成: {self.stats['total_checks']}项检查 / {self.stats['issues_found']}个问题")
        for sev in ['P0', 'P1', 'P2']:
            if self.stats['by_severity'][sev]:
                print(f"  {sev}: {self.stats['by_severity'][sev]}个")
        print(f"{'─'*60}")

        return self._generate_report()

    def _add_issue(self, rule_id, desc, severity, detail='', source=''):
        self.issues.append({
            'rule_id': rule_id,
            'desc': desc,
            'severity': severity,
            'detail': str(detail)[:500],
            'source': source,
            'agent': self.agent_name or 'unknown',
            'timestamp': datetime.now(CST).isoformat(),
        })
        self.stats['issues_found'] += 1
        self.stats['by_severity'][severity] += 1

    def _load_findings(self):
        """加载项目发现文件。"""
        findings = []
        if self.findings_dir.exists():
            agent_pattern = f"{self.agent_name}_*.json" if self.agent_name else "*.json"
            for f in sorted(self.findings_dir.glob(agent_pattern)):
                try:
                    with open(f, 'r', encoding='utf-8') as fh:
                        data = json.load(fh)
                        if isinstance(data, list):
                            findings.extend(data)
                        elif isinstance(data, dict):
                            findings.append(data)
                except Exception as e:
                    self._add_issue('R001_empty_finding', f'无法解析发现文件: {f.name}', 'P0', str(e))
        return findings

    def _check_format(self):
        """格式与协议规则检测。"""
        print("[规则包1] 格式与协议检测...")
        findings = self._load_findings()

        if not findings:
            self.stats['total_checks'] += 1
            print("  ⚠️  无发现文件，跳过格式检测")
            return

        # 读取原始Agent输出（如果有日志文件）
        raw_outputs = []
        agent_spec_dir = self.project_dir / 'agent_outputs'
        if self.agent_name and agent_spec_dir.exists():
            for f in agent_spec_dir.glob(f'{self.agent_name}*.txt'):
                try:
                    raw_outputs.append(f.read_text(encoding='utf-8'))
                except:
                    pass

        for finding in findings:
            self.stats['total_checks'] += 1

            # R001: 必填字段检查
            if isinstance(finding, dict):
                missing = [f for f in self.FORMAT_RULES['R001_empty_finding']['required_fields']
                           if f not in finding or not finding[f]]
                if missing:
                    self._add_issue('R001_empty_finding',
                                    f'发现记录缺少字段: {", ".join(missing)}',
                                    'P0',
                                    finding.get('title', finding.get('id', 'unknown')))

            # R004: 缺少ID
            if isinstance(finding, dict) and not finding.get('id'):
                self._add_issue('R004_missing_finding_id',
                                '发现记录缺少ID',
                                'P0',
                                finding.get('title', ''))

            # R006: 严重程度检查
            if isinstance(finding, dict):
                sev = finding.get('severity', '')
                if sev and sev not in ['P0', 'P1', 'P2', 'OBS']:
                    self._add_issue('R006_invalid_severity',
                                    f'无效的严重程度: {sev}',
                                    'P1',
                                    finding.get('id', ''))

        # R005: 重复ID检测
        ids = [f.get('id') for f in findings if isinstance(f, dict) and f.get('id')]
        dupes = [i for i in set(ids) if ids.count(i) > 1]
        for dup in dupes:
            self._add_issue('R005_duplicate_finding_id',
                            f'发现ID重复: {dup}',
                            'P1')

        # R002: 金额单位检查
        for i, finding in enumerate(findings):
            text = json.dumps(finding, ensure_ascii=False) if isinstance(finding, dict) else str(finding)
            if '万元' in text and re.search(r'\d{4,}\s*元(?![\w/])', text):
                self._add_issue('R002_amount_unit',
                                '金额单位可能混用（同时出现"元"和"万元"）',
                                'P1',
                                finding.get('id', f'finding_{i}') if isinstance(finding, dict) else f'finding_{i}')

        # R003: 日期格式检查
        for text in raw_outputs:
            bad_dates = re.findall(r'(\d{4}[/.]\d{1,2}[/.]\d{1,2})', text)
            if len(bad_dates) > 3:
                self._add_issue('R003_date_format',
                                f'发现{len(bad_dates)}处非标准日期格式',
                                'P2',
                                bad_dates[:5])

        n = len(self.issues) - self.stats['issues_found'] + (self.stats['issues_found'] or 0)
        print(f"  ✅ 格式检测完成")

    def _check_logic(self):
        """逻辑一致性检测。"""
        print("[规则包2] 逻辑一致性检测...")
        findings = self._load_findings()
        raw_outputs = []
        agent_spec_dir = self.project_dir / 'agent_outputs'
        if self.agent_name and agent_spec_dir.exists():
            for f in agent_spec_dir.glob(f'{self.agent_name}*.txt'):
                try:
                    raw_outputs.append(f.read_text(encoding='utf-8'))
                except:
                    pass
        combined = ' '.join(raw_outputs)

        # R101: 自相矛盾检测
        pos = self.LOGIC_RULES['R101_self_contradiction']['keywords_positive']
        neg = self.LOGIC_RULES['R101_self_contradiction']['keywords_negative']
        found_pos = [k for k in pos if k in combined]
        found_neg = [k for k in neg if k in combined]
        if found_pos and found_neg and len(combined) < 10000:
            # 在同一份较短输出中同时出现正负两面关键词
            self._add_issue('R101_self_contradiction',
                            'Agent输出可能自相矛盾（同时出现正面和负面关键词）',
                            'P0',
                            f'正面: {found_pos[:3]} | 负面: {found_neg[:3]}')
        self.stats['total_checks'] += 1

        # R103: 结论缺证据
        conclusion_kw = self.LOGIC_RULES['R103_conclusion_without_evidence']['conclusion_keywords']
        for kw in conclusion_kw:
            for match in re.finditer(kw, combined):
                pos = match.start()
                nearby = combined[max(0, pos-200):pos+200]
                if '凭证' not in nearby and '合同' not in nearby and '证据' not in nearby and '依据' not in nearby:
                    self._add_issue('R103_conclusion_without_evidence',
                                    f'结论关键词"{kw}"附近200字符内未找到证据引用',
                                    'P2',
                                    nearby[:100])
                    break
        self.stats['total_checks'] += 1

        # R104: 过早声明成功
        success_markers = self.LOGIC_RULES['R104_premature_success']['success_markers']
        # 如果发现数=0但声明了完成，可能是过早成功
        if len(findings) == 0:
            for pattern in success_markers:
                if re.search(pattern, combined):
                    self._add_issue('R104_premature_success',
                                    f'任务可能过早声明完成（发现数=0但输出包含"{pattern}"）',
                                    'P0')
                    break
        self.stats['total_checks'] += 1

        print(f"  ✅ 逻辑检测完成")

    def _check_audit(self):
        """审计专项规则检测。"""
        print("[规则包3] 审计专项检测...")
        findings = self._load_findings()

        for finding in findings:
            if not isinstance(finding, dict):
                continue
            text = json.dumps(finding, ensure_ascii=False)

            # R201: 严重程度虚高
            low_kw = self.AUDIT_RULES['R201_severity_inflation']['low_impact_keywords']
            sev = finding.get('severity', '')
            desc = finding.get('description', '') + finding.get('title', '')
            if sev in ['P0', 'P1']:
                if any(kw in desc for kw in low_kw):
                    self._add_issue('R201_severity_inflation',
                                    f'可能严重程度虚高："{sev}"但涉及"{desc[:50]}"',
                                    'P2',
                                    finding.get('id', ''))

            # R204: 缺少取证来源
            has_source = False
            for src_pattern in self.AUDIT_RULES['R204_missing_audit_trail']['required_sources']:
                if src_pattern in text:
                    has_source = True
                    break
            if not has_source and finding.get('severity') in ['P0', 'P1']:
                self._add_issue('R204_missing_audit_trail',
                                'P0/P1级发现缺少取证来源标注',
                                'P1',
                                finding.get('id', ''))

            # R203: 金额范围检查
            m = re.search(r'(\d{9,})', text)
            if m:
                amount = int(m.group(1))
                if amount > self.AUDIT_RULES['R203_amount_range_check']['reasonable_max']:
                    self._add_issue('R203_amount_range_check',
                                    f'金额超出合理范围: {amount}',
                                    'P1',
                                    finding.get('id', ''))

            # R205: 缺少整改建议
            if finding.get('severity') in ['P0', 'P1']:
                if '建议' not in text and 'recommend' not in text.lower() and '措施' not in text:
                    self._add_issue('R205_finding_no_recommendation',
                                    'P0/P1级发现缺少整改建议',
                                    'P2',
                                    finding.get('id', ''))

            self.stats['total_checks'] += 1

        print(f"  ✅ 审计专项检测完成")

    def _check_handover(self):
        """多Agent交接异常检测。"""
        print("[规则包4] 多Agent交接检测...")
        if not self.handover_dir.exists():
            self.stats['total_checks'] += 1
            print("  ⚠️  无交接包，跳过交接检测")
            return

        handovers = []
        for f in sorted(self.handover_dir.glob('H-*.json')):
            try:
                handovers.append(json.loads(f.read_text(encoding='utf-8')))
            except:
                pass

        if not handovers:
            self.stats['total_checks'] += 1
            return

        # R301: 交接包关键字段检查
        required = self.HANDOVER_RULES['R301_handover_info_loss']['required_handover_fields']
        for hp in handovers:
            for field in required:
                if not hp.get(field):
                    self._add_issue('R301_handover_info_loss',
                                    f'交接包 {hp.get("handover_id", "?")} 缺少关键字段: {field}',
                                    'P0',
                                    hp.get('source_agent', ''))

        # R305: 交接链断裂检测
        sources = set(hp.get('source_agent') for hp in handovers)
        agents_with_parent = set()
        for hp in handovers:
            parent = hp.get('parent_handover')
            if parent:
                agents_with_parent.add(hp.get('source_agent'))
                # 检查父包是否存在
                if not any(h.get('handover_id') == parent for h in handovers):
                    self._add_issue('R305_chain_break',
                                    f'交接链断裂: {hp.get("source_agent")} 引用了不存在的 parent_handover {parent}',
                                    'P0')

        # R303: 警告被忽略检测
        for hp in handovers:
            if hp.get('warnings'):
                # 检查下一个Agent是否响应了警告
                next_agent = hp.get('source_agent')  # 简化处理
                if hp.get('findings_summary', {}).get('total', 0) == 0:
                    self._add_issue('R303_warning_ignored',
                                    f'{hp.get("source_agent")}的{warnings_count}条警告可能未被后续Agent响应',
                                    'P1',
                                    hp.get('handover_id', ''))

        self.stats['total_checks'] += len(handovers)
        print(f"  ✅ 交接检测完成 ({len(handovers)}个交接包)")

    def _generate_report(self):
        """生成检测报告。"""
        report = {
            'tool': 'agent_debug_rules',
            'project': self.project_slug,
            'agent': self.agent_name,
            'timestamp': datetime.now(CST).isoformat(),
            'stats': dict(self.stats),
            'issues': self.issues,
        }

        # 保存
        report_path = DEBUG_DIR / f'rules_{self.project_slug}_{datetime.now(CST).strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 保存Markdown
        md_path = report_path.with_suffix('.md')
        self._generate_markdown(md_path)

        print(f"\n📄 报告已保存: {report_path}")
        print(f"📄 Markdown: {md_path}")
        return report

    def _generate_markdown(self, path):
        issues_by_sev = defaultdict(list)
        for issue in self.issues:
            issues_by_sev[issue['severity']].append(issue)

        lines = [
            f"# Agent确定性规则检测报告",
            f"",
            f"**项目**: {self.project_slug} | **Agent**: {self.agent_name or '全部'}",
            f"**时间**: {datetime.now(CST).strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"## 概览",
            f"",
            f"| 指标 | 值 |",
            f"|:-----|:---|",
            f"| 检查项 | {self.stats['total_checks']} |",
            f"| 发现问题 | {self.stats['issues_found']} |",
        ]
        for sev in ['P0', 'P1', 'P2']:
            if self.stats['by_severity'][sev]:
                lines.append(f"| {sev} | {self.stats['by_severity'][sev]} |")
        lines.append("")

        for sev in ['P0', 'P1', 'P2']:
            if issues_by_sev[sev]:
                lines.append(f"## {sev} 级问题 ({len(issues_by_sev[sev])})")
                lines.append("")
                lines.append("| 规则 | 描述 | 详情 |")
                lines.append("|:-----|:-----|:-----|")
                for issue in issues_by_sev[sev]:
                    lines.append(f"| {issue['rule_id']} | {issue['desc']} | {issue['detail'][:80]} |")
                lines.append("")

        lines.append("---")
        lines.append("*由 agent_debug_rules.py 自动生成（确定性规则，未调用LLM）*")

        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Agent确定性规则检测')
    parser.add_argument('--project', required=True, help='项目标识')
    parser.add_argument('--agent', default=None, help='目标Agent名称')
    args = parser.parse_args()

    checker = AgentDebugRules(args.project, args.agent)
    checker.run_all()

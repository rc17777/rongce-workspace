# -*- coding: utf-8 -*-
"""
DeepDebug交接点定位引擎 v1.0
=============================
灵感来源：AgentDebugX 的 DeepDebug 多轮根因诊断

对标 DeepDebug 三步策略：
  1. 全局轨迹读取 → 建立整体理解
  2. 结构引导探查 → 多Agent追踪交接点 / 单Agent二分法缩小范围
  3. 交叉验证 → 输出可审计报告（责任Agent+步骤+证据+修复方案）

用法：
  python agent_deep_debug.py --project "XX项目" --mode deepdebug
  python agent_deep_debug.py --project "XX项目" --mode binary --error-step 10
  python agent_deep_debug.py --project "XX项目" --mode handover --suspect-agent "data_scout"
"""

import os, sys, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
DEBUG_DIR = BLACKBOARD / 'debug'

ROOT_CAUSE_PATTERNS = {
    'handover_context_loss': {
        'id': 'RC001',
        'desc': '交接上下文丢失',
        'signals': ['context_snapshot缺失', 'confirmed_facts为空', 'goal不明确'],
        'fix': '在handover_protocol.emit时强制填充goal和confirmed_facts字段',
    },
    'finding_dropped_in_transit': {
        'id': 'RC002',
        'desc': '发现被传递过程中丢失',
        'signals': ['前Agent发现数>后Agent引用数', 'warnings中标记但未出现'],
        'fix': '在handover_hook中增加发现追踪ID，下游Agent必须逐条确认',
    },
    'coordinate_mismatch': {
        'id': 'RC003',
        'desc': '坐标系分配错误',
        'signals': ['Agent任务不匹配坐标系', 'Agent spec未列出该坐标系'],
        'fix': '重新运行penetrate阶段，检查COORDINATE_AGENT_MAP配置',
    },
    'early_termination': {
        'id': 'RC004',
        'desc': 'Agent过早终止（对标AgentDebugX premature success）',
        'signals': ['发现数为零但数据量充足', '输出包含"未发现异常"但raw_data有相关文件'],
        'fix': '检查Agent的任务prompt是否包含明确的"不得提前结束"约束',
    },
    'data_format_confusion': {
        'id': 'RC005',
        'desc': 'Agent对数据格式理解错误',
        'signals': ['金额数量级异常', '日期解析错误', '列名映射失败'],
        'fix': '在Agent spec中增加data_schema字段，指定期望的数据格式',
    },
    'model_hallucination': {
        'id': 'RC006',
        'desc': '模型幻觉（编造不存在的法规/数据）',
        'signals': ['引用的法规号不存在', '金额与源文件不一致', '人名/地名错误'],
        'fix': '增加RAG约束（法规引用必须来自RAG检索结果），或切换更高精度模型',
    },
    'tool_call_error': {
        'id': 'RC007',
        'desc': '工具调用格式错误（对标AgentDebugX）',
        'signals': ['JSON解析失败', '参数类型不匹配', '缺少必填参数'],
        'fix': '在Agent spec中增加tool_schema字段，增加预处理校验层',
    },
    'severity_misclassification': {
        'id': 'RC008',
        'desc': '严重程度分类错误',
        'signals': ['P0标记的是格式问题', 'P2标记的是资金挪用'],
        'fix': '在Agent spec中增加severity_guide，或增加后处理规则修正',
    },
}


class DeepDebugger:
    """
    DeepDebug 交接点定位引擎。
    对标 AgentDebugX 的 Attribute 阶段——从"看到错误"到"找到根因"。
    """

    def __init__(self, project_slug):
        self.project_slug = project_slug
        self.project_dir = PROJECTS / project_slug
        self.handover_dir = self.project_dir / 'handovers'
        self.findings_dir = self.project_dir / 'findings'
        self.status_path = self.project_dir / 'status.json'
        self.trace = []  # 诊断过程记录

    def run_deepdebug(self):
        """完整 DeepDebug 流程：三步骤。"""
        print(f"\n{'='*60}")
        print(f"🔬 DeepDebug 深度诊断 — {self.project_slug}")
        print(f"{'='*60}\n")

        # Step 1: 全局轨迹读取
        print("[Step 1/3] 全局轨迹读取...")
        overview = self._global_trace_read()
        print(f"  交接包: {overview['handover_count']}个")
        print(f"  Agent: {', '.join(overview['agents'])}")
        print(f"  总疑点: {overview['total_findings']}条")
        print(f"  异常信号: {len(overview['anomaly_signals'])}个")

        if overview['anomaly_signals']:
            for sig in overview['anomaly_signals']:
                print(f"    🚨 {sig}")

        # Step 2: 结构引导探查
        print(f"\n[Step 2/3] 结构引导探查...")
        suspect_agents = self._structured_probe(overview)
        if suspect_agents:
            print(f"  嫌疑Agent: {', '.join(suspect_agents)}")
        else:
            print(f"  未发现明显嫌疑Agent")

        # Step 3: 交叉验证
        print(f"\n[Step 3/3] 交叉验证...")
        report = self._cross_validate(overview, suspect_agents)

        # 输出报告
        self._output_report(report)
        return report

    def _global_trace_read(self):
        """Step 1: 读取所有交接包和发现，建立全局视图。"""
        overview = {
            'handover_count': 0,
            'agents': [],
            'total_findings': 0,
            'findings_by_agent': {},
            'warnings_pool': [],
            'anomaly_signals': [],
            'chain_length': 0,
            'handover_gaps': [],
        }

        # 读取交接包
        handovers = []
        if self.handover_dir.exists():
            for f in sorted(self.handover_dir.glob('H-*.json')):
                try:
                    hp = json.loads(f.read_text(encoding='utf-8'))
                    handovers.append(hp)
                except:
                    pass

        overview['handover_count'] = len(handovers)
        overview['agents'] = list(set(hp.get('source_agent', '?') for hp in handovers))
        overview['total_findings'] = sum(hp.get('findings_summary', {}).get('total', 0) for hp in handovers)

        # 各Agent发现数
        for hp in handovers:
            agent = hp.get('source_agent', '?')
            count = hp.get('findings_summary', {}).get('total', 0)
            overview['findings_by_agent'][agent] = overview['findings_by_agent'].get(agent, 0) + count

        # 收集所有警告
        for hp in handovers:
            overview['warnings_pool'].extend(hp.get('warnings', []))

        # 检测异常信号
        overview['anomaly_signals'] = self._detect_anomaly_signals(handovers, overview)

        # 检测交接链
        overview['chain_length'] = len(handovers)
        parent_ids = set()
        for hp in handovers:
            parent = hp.get('parent_handover')
            if parent:
                overview['handover_gaps'].append({
                    'agent': hp.get('source_agent'),
                    'parent': parent,
                    'parent_exists': any(h.get('handover_id') == parent for h in handovers),
                })

        self.trace.append({'step': 1, 'action': 'global_trace_read', 'findings': overview['anomaly_signals']})
        return overview

    def _detect_anomaly_signals(self, handovers, overview):
        """从交接包中提取异常信号。"""
        signals = []

        # 信号1: Agent发现数为零但有大量警告
        for hp in handovers:
            if hp.get('findings_summary', {}).get('total', 0) == 0 and len(hp.get('warnings', [])) > 2:
                signals.append(f"{hp['source_agent']}: 发现0条疑点但有{len(hp['warnings'])}条警告 → 可能过早终止")

        # 信号2: 关键字段缺失
        for hp in handovers:
            missing = []
            if not hp.get('goal'):
                missing.append('goal')
            if not hp.get('confirmed_facts'):
                missing.append('confirmed_facts')
            if not hp.get('context_snapshot'):
                missing.append('context_snapshot')
            if missing:
                signals.append(f"{hp['source_agent']}: 交接包缺少 {', '.join(missing)} → 上下文丢失")

        # 信号3: 发现总数异常
        if overview['total_findings'] == 0 and overview['handover_count'] > 0:
            signals.append("所有Agent均未发现疑点 → 可能整体审计逻辑有问题")

        # 信号4: 单个Agent发现过多（可能把无关信息当疑点）
        for agent, count in overview['findings_by_agent'].items():
            if count > 50:
                signals.append(f"{agent}: 发现{count}条疑点 → 可能严重程度分类失控")

        # 信号5: 交接链断裂
        parent_ids = set(hp.get('parent_handover') for hp in handovers if hp.get('parent_handover'))
        existing_ids = set(hp.get('handover_id') for hp in handovers)
        broken = parent_ids - existing_ids
        if broken:
            signals.append(f"交接链断裂，引用了{len(broken)}个不存在的父包")

        return signals

    def _structured_probe(self, overview):
        """Step 2: 结构引导探查——定位嫌疑Agent。"""
        suspect_agents = set()

        # 检查1: 交接点信息丢失
        for gap in overview.get('handover_gaps', []):
            if not gap.get('parent_exists'):
                suspect_agents.add(gap['agent'])
                self.trace.append({'step': 2, 'check': 'handover_gap', 'agent': gap['agent'], 'result': '交接链断裂'})

        # 检查2: 发现数异常
        for agent, count in overview['findings_by_agent'].items():
            if count == 0:
                suspect_agents.add(agent)
                self.trace.append({'step': 2, 'check': 'zero_findings', 'agent': agent, 'result': '发现数为零'})

        # 检查3: 检查findings目录中实际文件
        if self.findings_dir.exists():
            actual_files = list(self.findings_dir.glob('*.json'))
            agents_with_files = set()
            for f in actual_files:
                # 从文件名解析Agent名
                parts = f.stem.split('_')
                if parts:
                    agents_with_files.add(parts[0])

            # Agent在交接包中但findings目录无对应文件
            for agent in overview['agents']:
                if agent not in agents_with_files:
                    suspect_agents.add(agent)
                    self.trace.append({'step': 2, 'check': 'missing_file', 'agent': agent, 'result': '交接包存在但findings文件缺失'})

        return list(suspect_agents)

    def _cross_validate(self, overview, suspect_agents):
        """Step 3: 交叉验证——对冲突候选根因交叉检验。"""
        report = {
            'project': self.project_slug,
            'timestamp': datetime.now(CST).isoformat(),
            'diagnosis': {
                'root_causes': [],
                'confidence': 'medium',
            },
            'evidence': [],
            'fix_plan': [],
            'trace': self.trace,
        }

        for agent in suspect_agents:
            root_cause = self._match_root_cause(agent, overview)
            report['diagnosis']['root_causes'].append({
                'agent': agent,
                'cause': root_cause,
                'confidence': self._estimate_confidence(agent, root_cause),
            })

        # 生成修复计划
        for rc in report['diagnosis']['root_causes']:
            fix = self._generate_fix(rc['cause'])
            if fix:
                report['fix_plan'].append(fix)

        # 去重
        seen = set()
        unique_fixes = []
        for fix in report['fix_plan']:
            if fix['action'] not in seen:
                seen.add(fix['action'])
                unique_fixes.append(fix)
        report['fix_plan'] = unique_fixes

        return report

    def _match_root_cause(self, agent, overview):
        """将Agent匹配到已知根因模式。"""
        scores = defaultdict(int)

        findings_count = overview['findings_by_agent'].get(agent, 0)

        if findings_count == 0:
            scores['RC004'] += 2  # early_termination
            scores['RC001'] += 1  # context_loss

        # 检查warnings
        for hp_json in self.handover_dir.glob('H-*.json') if self.handover_dir.exists() else []:
            try:
                hp = json.loads(hp_json.read_text(encoding='utf-8'))
                if hp.get('source_agent') == agent:
                    if len(hp.get('warnings', [])) > 0:
                        scores['RC001'] += 1
                    if not hp.get('goal'):
                        scores['RC001'] += 2
                    if not hp.get('confirmed_facts'):
                        scores['RC001'] += 1
            except:
                pass

        best_match = max(scores, key=scores.get) if scores else 'RC000'
        return ROOT_CAUSE_PATTERNS.get(best_match, {'id': 'RC000', 'desc': '未分类', 'fix': '需人工分析'})

    def _estimate_confidence(self, agent, root_cause):
        """估计归因置信度。"""
        rc_id = root_cause.get('id', 'RC000')

        # 高置信度模式
        high_confidence = ['RC001', 'RC004', 'RC005', 'RC007']
        medium_confidence = ['RC002', 'RC003', 'RC006', 'RC008']

        if rc_id in high_confidence:
            return 'high'
        elif rc_id in medium_confidence:
            return 'medium'
        return 'low'

    def _generate_fix(self, root_cause):
        """根据根因生成修复方案。"""
        cause_id = root_cause.get('id', '')
        if cause_id == 'RC001':
            return {
                'action': '补填交接包关键字段',
                'command': 'python handover_protocol.py emit --project "PROJECT" --agent "AGENT" --goal "..." --facts ...',
                'detail': '强制填充goal/confirmed_facts/context_snapshot后再emit',
                'auto_fix': False,
            }
        elif cause_id == 'RC004':
            return {
                'action': '检查Agent prompt约束',
                'command': 'python agent_debug_rules.py --project "PROJECT" --agent "AGENT"',
                'detail': '在Agent spec中增加"不得在未完成全部检查前声明无异常"的约束',
                'auto_fix': False,
            }
        elif cause_id == 'RC002':
            return {
                'action': '启用发现追踪ID',
                'command': 'python handover_hook.py --project "PROJECT" --agent "AGENT" --track-ids',
                'detail': '在handover中增加finding_id列表并在下游Agent中逐条确认',
                'auto_fix': True,
            }
        elif cause_id == 'RC005':
            return {
                'action': '修正Agent数据格式配置',
                'detail': '在Agent spec中增加data_schema字段，指定列名映射和单位',
                'auto_fix': False,
            }
        elif cause_id == 'RC006':
            return {
                'action': '增加RAG约束或切换模型',
                'command': 'python orchestrate_v3.py penetrate "PROJECT"  # 用RAG增强上下文',
                'detail': '法规引用必须来自RAG检索结果，或切换到sonnet-5等低幻觉模型',
                'auto_fix': False,
            }
        elif cause_id == 'RC007':
            return {
                'action': '增加工具调用预处理校验层',
                'detail': '在Agent spec中增加tool_schema字段，调用前做JSON Schema校验',
                'auto_fix': True,
            }
        return None

    def run_binary_search(self, error_step):
        """二分法归因（单体Agent用）。"""
        print(f"\n{'='*60}")
        print(f"🔍 二分法归因 — {self.project_slug} | 错误步骤: {error_step}")
        print(f"{'='*60}\n")

        # 读取所有发现
        findings = []
        if self.findings_dir.exists():
            for f in sorted(self.findings_dir.glob('*.json')):
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    if isinstance(data, list):
                        findings.extend(data)
                    elif isinstance(data, dict):
                        for k, v in data.items():
                            if k == 'steps':
                                findings.extend(v)
                except:
                    pass

        if not findings:
            print("无发现文件，无法进行二分法归因")
            return

        total = len(findings)
        print(f"总共 {total} 个发现步骤，二分搜索中...")

        def check_range(start, end):
            """检查该范围的步骤是否有异常。"""
            subset = findings[start:end]
            issues = 0
            for item in subset:
                if isinstance(item, dict):
                    sev = item.get('severity', '')
                    if sev in ['P0', 'P1']:
                        issues += 1
                    # 检查是否有错误标记
                    text = json.dumps(item, ensure_ascii=False)
                    if any(kw in text for kw in ['error', '失败', '异常', '不符合', '违规']):
                        issues += 1
            return issues

        # 二分搜索
        lo, hi = 0, total
        iterations = 0
        while lo < hi and iterations < 20:
            mid = (lo + hi) // 2
            left_issues = check_range(lo, mid)
            right_issues = check_range(mid, hi)
            iterations += 1

            print(f"  [{iterations}] 范围 [{lo}-{mid})={left_issues}问题 | [{mid}-{hi})={right_issues}问题")

            if left_issues > right_issues:
                hi = mid
            elif right_issues > left_issues:
                lo = mid
            else:
                # 两边一样多，检查哪边有P0
                left_p0 = sum(1 for f in findings[lo:mid] if isinstance(f, dict) and f.get('severity') == 'P0')
                right_p0 = sum(1 for f in findings[mid:hi] if isinstance(f, dict) and f.get('severity') == 'P0')
                if left_p0 > right_p0:
                    hi = mid
                elif right_p0 > left_p0:
                    lo = mid
                else:
                    # 缩小误差步附近
                    if lo <= error_step < mid:
                        hi = mid
                    else:
                        lo = mid

        suspect_range = findings[max(0, lo-2):min(total, hi+2)]
        print(f"\n📌 嫌疑范围: 步骤 {lo} ~ {hi}")
        for item in suspect_range:
            if isinstance(item, dict):
                print(f"   [{item.get('severity', '?')}] {item.get('title', item.get('id', str(item)[:80]))}")

        return {'range': [lo, hi], 'suspects': suspect_range}

    def run_handover_probe(self, suspect_agent):
        """针对特定嫌疑Agent的交接点探查。"""
        print(f"\n{'='*60}")
        print(f"🔍 交接点探查 — {self.project_slug} | 嫌疑Agent: {suspect_agent}")
        print(f"{'='*60}\n")

        if not self.handover_dir.exists():
            print("无交接包，无法探查")
            return

        # 找出所有涉及该Agent的交接
        related = []
        for f in sorted(self.handover_dir.glob('H-*.json')):
            try:
                hp = json.loads(f.read_text(encoding='utf-8'))
                if hp.get('source_agent') == suspect_agent:
                    related.append(hp)
            except:
                pass

        if not related:
            print(f"未找到 {suspect_agent} 的交接包")
            return

        print(f"找到 {len(related)} 个相关交接包\n")

        for hp in related:
            print(f"── {hp['handover_id']} ──")
            print(f"  目标: {hp.get('goal', '未指定')[:100]}")
            print(f"  已确认事实: {len(hp.get('confirmed_facts', []))}条")
            print(f"  已完成检查: {len(hp.get('completed_checks', []))}项")
            print(f"  待处理: {len(hp.get('pending_checks', []))}项")
            print(f"  发现: {hp.get('findings_summary', {}).get('total', 0)}条")
            print(f"  警告: {len(hp.get('warnings', []))}条")
            if hp.get('warnings'):
                for w in hp['warnings'][:3]:
                    print(f"    ⚠️  {w}")
            print(f"  上下文: {hp.get('context_snapshot', '无')[:150]}")
            print()

        # 给出诊断建议
        total_findings = sum(hp.get('findings_summary', {}).get('total', 0) for hp in related)
        total_warnings = sum(len(hp.get('warnings', [])) for hp in related)
        total_facts = sum(len(hp.get('confirmed_facts', [])) for hp in related)

        print("诊断建议:")
        if total_findings == 0 and total_facts > 0:
            print("  🚨 Agent有信息输入但没有输出发现 → 可能过早终止或数据理解错误")
            print("  建议: 检查Agent prompt，确认任务定义和数据schema匹配")
        elif total_warnings > total_findings * 2:
            print("  ⚠️  警告数远超发现数 → Agent遇到了大量异常但未正确处理")
            print("  建议: 检查Agent的错误处理逻辑，可能需要调整容错策略")
        elif total_facts == 0:
            print("  ⚠️  Agent没有任何已确认事实 → 可能没有读取上游交接包")
            print("  建议: 检查handover_protocol的context读取是否正确")
        else:
            print("  ✅ 未发现明显异常的交接模式")

    def _output_report(self, report):
        """输出诊断报告。"""
        # JSON
        report_path = DEBUG_DIR / f'deepdebug_{self.project_slug}_{datetime.now(CST).strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Markdown
        md_path = report_path.with_suffix('.md')
        lines = [
            f"# DeepDebug 根因诊断报告",
            f"",
            f"**项目**: {self.project_slug}",
            f"**时间**: {datetime.now(CST).strftime('%Y-%m-%d %H:%M')}",
            f"**诊断步骤**: {len(report.get('trace', []))}步",
            f"",
            f"## 诊断结论",
            f"",
            f"| Agent | 根因 | 置信度 |",
            f"|:------|:-----|:------:|",
        ]
        for rc in report['diagnosis']['root_causes']:
            cause = rc['cause']
            lines.append(f"| {rc['agent']} | {cause.get('desc', cause.get('id'))} | {rc.get('confidence', '?')} |")
        lines.append("")

        if report['fix_plan']:
            lines.append("## 修复方案")
            lines.append("")
            for i, fix in enumerate(report['fix_plan'], 1):
                auto = "🤖可自动" if fix.get('auto_fix') else "👤需人工"
                lines.append(f"### {i}. {fix['action']} {auto}")
                lines.append(f"")
                lines.append(f"{fix['detail']}")
                if fix.get('command'):
                    lines.append(f"")
                    lines.append(f"```bash")
                    lines.append(f"{fix['command']}")
                    lines.append(f"```")
                lines.append("")

        lines.append("---")
        lines.append("*由 agent_deep_debug.py 自动生成（规则引擎，未调用LLM）*")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"\n📄 诊断报告: {report_path}")
        print(f"📄 Markdown: {md_path}")


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='DeepDebug 根因定位引擎')
    parser.add_argument('--project', required=True)
    parser.add_argument('--mode', choices=['deepdebug', 'binary', 'handover'], default='deepdebug')
    parser.add_argument('--error-step', type=int, default=0, help='二分法模式下的错误步骤')
    parser.add_argument('--suspect-agent', default=None, help='交接探查模式下的嫌疑Agent')
    args = parser.parse_args()

    debugger = DeepDebugger(args.project)

    if args.mode == 'deepdebug':
        debugger.run_deepdebug()
    elif args.mode == 'binary':
        debugger.run_binary_search(args.error_step)
    elif args.mode == 'handover':
        if not args.suspect_agent:
            print("⚠️  handover模式需要 --suspect-agent 参数")
        else:
            debugger.run_handover_probe(args.suspect_agent)

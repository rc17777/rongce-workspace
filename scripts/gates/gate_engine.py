"""审盾 Gate Engine — HARD-GATE 执行引擎

可执行的验证门系统，确保 AI 审计 Agent 遵循工程纪律。
每个 Gate 对应一个 Skill 的 HARD-GATE，未通过则拦截后续操作。

用法:
    python gate_engine.py --project "某项目" --gate preaudit
    python gate_engine.py --project "某项目" --gate evidence --findings findings.json
"""
import json, os, sys, re, argparse
sys.stdout.reconfigure(encoding='utf-8')

GATES_DIR = os.path.dirname(__file__)
PROJECTS_BASE = os.path.abspath(
    os.path.join(GATES_DIR, '..', '..', 'audit-blackboard', 'projects')
)


class GateResult:
    """Gate 执行结果"""
    def __init__(self, gate_name: str):
        self.gate_name = gate_name
        self.passed = True
        self.checks = []
        self.blocked_by = []
        self.suggested_action = ''

    def fail(self, check_name: str, detail: str, suggestion: str = ''):
        self.passed = False
        self.checks.append({
            'check': check_name,
            'status': 'fail',
            'detail': detail
        })
        self.blocked_by.append(check_name)
        if suggestion and not self.suggested_action:
            self.suggested_action = suggestion

    def pass_check(self, check_name: str, detail: str = ''):
        self.checks.append({
            'check': check_name,
            'status': 'pass',
            'detail': detail
        })

    def to_dict(self) -> dict:
        return {
            'gate': self.gate_name,
            'passed': self.passed,
            'blocked_by': self.blocked_by,
            'checks': self.checks,
            'suggested_action': self.suggested_action,
        }

    def print_report(self):
        status = '✅ PASS' if self.passed else '❌ BLOCKED'
        print(f'\n  [GATE] {self.gate_name} → {status}')
        for c in self.checks:
            icon = '✅' if c['status'] == 'pass' else '❌'
            detail = f" — {c['detail']}" if c['detail'] else ''
            print(f'    {icon} {c["check"]}{detail}')
        if self.blocked_by:
            print(f'  🚫 拦截项: {", ".join(self.blocked_by)}')
        if self.suggested_action:
            print(f'  💡 建议: {self.suggested_action}')
        return self.passed


def get_project_dir(project_name: str) -> str:
    """获取项目目录"""
    # 支持带路径的项目名
    if os.path.isdir(project_name):
        return os.path.abspath(project_name)
    return os.path.join(PROJECTS_BASE, project_name)


# ============================================================
# Skill 1: 审前策划 Gate
# ============================================================

def gate_preaudit(project_name: str) -> GateResult:
    """审前策划 HARD-GATE：方案未经确认，不得进场

    检查项目是否存在已确认的审计实施方案。
    """
    result = GateResult('审前策划')

    project_dir = get_project_dir(project_name)
    result.pass_check('项目目录', project_dir)

    # Check 1: 项目目录是否存在
    if not os.path.isdir(project_dir):
        result.fail('项目目录存在', f'目录不存在: {project_dir}',
                     f'请先创建项目: mkdir -p "{project_dir}"')
        # 目录都不存在，后面不用检查了
        result.suggested_action = '请先通过平台创建项目或指定正确的项目名称'
        return result

    # Check 2: 查找方案文件（支持多种命名格式）
    plan_files = []
    for root, dirs, files in os.walk(project_dir):
        for f in files:
            if re.match(r'.*(方案|plan|审计实施)[^.]*\.(md|docx?|pdf)', f, re.I):
                plan_files.append(os.path.join(root, f))

    if not plan_files:
        result.fail('方案文件存在', '未找到审计实施方案文件',
                     '请先撰写审计实施方案，支持格式: 方案.md / 审计实施方案.docx / plan.md')
        return result

    # 取最新的方案文件
    plan_path = max(plan_files, key=os.path.getmtime)
    plan_size = os.path.getsize(plan_path)
    plan_mtime = os.path.getmtime(plan_path)
    result.pass_check('方案文件存在',
                       f'{os.path.relpath(plan_path, project_dir)} ({plan_size/1024:.0f}KB)')

    # Check 3: 方案文件是否为空
    if plan_size < 50:
        result.fail('方案内容非空', f'方案文件过小 ({plan_size}B)，可能为空')

    # Check 4: 方案是否包含必要要素
    if plan_path.endswith('.md') or plan_path.endswith('.txt'):
        with open(plan_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    else:
        # DOCX等二进制文件——尝试用python-docx
        try:
            from docx import Document
            doc = Document(plan_path)
            content = '\n'.join(p.text for p in doc.paragraphs)
        except:
            content = ''

    required_sections = {
        '审计目标': ['目标', '目的', 'objective'],
        '审计范围': ['范围', 'scope', '审计期间'],
        '审计程序': ['程序', '步骤', '方法', 'procedure'],
        '人员分工': ['人员', '分工', '组长', '组员'],
    }

    for section_name, keywords in required_sections.items():
        found = any(kw in content for kw in keywords)
        if found:
            result.pass_check(f'方案包含「{section_name}」')
        else:
            result.fail(f'方案包含「{section_name}」',
                        f'未找到相关关键词: {keywords[0]}',
                        f'请在方案中补充{section_name}章节')

    # Check 5: 方案是否已被确认（status.json中的confirmed标记）
    status_file = os.path.join(project_dir, 'status.json')
    confirmed = False
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            confirmed = status.get('plan_confirmed', False)
            confirmed_by = status.get('confirmed_by', '')
            confirmed_at = status.get('confirmed_at', '')
            detail = f'由 {confirmed_by} 于 {confirmed_at} 确认' if confirmed else '未确认'
            if confirmed:
                result.pass_check('方案已确认', detail)
            else:
                result.fail('方案已确认', 'status.json 中 plan_confirmed=false',
                             '请在 status.json 中设置 plan_confirmed=true')
        except:
            result.fail('方案确认状态可读取', 'status.json 解析失败')
    else:
        result.fail('方案确认状态', '未找到 status.json，无法判断方案是否已获确认',
                     f'请创建 {status_file} 并设置 plan_confirmed=true')

    # 最后检查：如果方案未确认，给出建议
    if not result.passed:
        result.suggested_action = result.suggested_action or (
            '请完成以下步骤后再进场:\n'
            f'  1. 撰写审计实施方案 → 保存到 {project_dir}/方案.md\n'
            f'  2. 确认方案包含：目标、范围、程序、人员\n'
            f'  3. 在 status.json 中标记 plan_confirmed=true')

    return result


# ============================================================
# Skill 4: 证据闭环 Gate
# ============================================================

def gate_evidence(project_name: str, findings_file: str = '') -> GateResult:
    """证据闭环 HARD-GATE：没有证据，不得宣称已确认

    检查审计发现是否有对应的取证证据、是否存在模糊表述、汇总数是否交叉验证。
    """
    result = GateResult('证据闭环')
    project_dir = get_project_dir(project_name)

    # Check 0: 项目目录
    if not os.path.isdir(project_dir):
        result.fail('项目目录存在', f'目录不存在: {project_dir}')
        return result

    # 查找发现文件
    findings_path = None
    if findings_file and os.path.exists(findings_file):
        findings_path = findings_file
    else:
        # 自动查找
        findings_dir = os.path.join(project_dir, 'findings')
        if os.path.isdir(findings_dir):
            jsons = [os.path.join(findings_dir, f)
                     for f in os.listdir(findings_dir)
                     if f.endswith('.json') and not f.startswith('_')]
            if jsons:
                findings_path = max(jsons, key=os.path.getmtime)

    if not findings_path:
        result.pass_check('发现文件存在', '未找到疑点/发现文件 — 可能是新项目（跳过证据检查）')
        # 新项目无发现时，证据门自动通过
        return result

    result.pass_check('发现文件存在', os.path.relpath(findings_path, project_dir))

    # 加载发现数据
    try:
        with open(findings_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        findings = json.loads(raw)
        if isinstance(findings, dict):
            findings = [findings]
    except Exception as e:
        result.fail('发现文件可解析', f'JSON解析失败: {e}')
        return result

    if not findings:
        result.pass_check('发现数量', '0条（跳过证据检查）')
        return result

    result.pass_check('发现数量', f'{len(findings)} 条')

    # 红词检查 —— 模糊表述
    red_flags = ['应该', '大概', '可能', '似乎', '也许', '看起来', '好像',
                 'we should', 'probably', 'seems', 'maybe', 'appears',
                 '我认为', '我们觉得', '据估计']

    for i, f in enumerate(findings):
        f_text = json.dumps(f, ensure_ascii=False)
        title = f.get('title', f.get('问题', f.get('finding', f'发现#{i+1}')))
        title_short = title[:40]

        # Check: 每条发现是否有证据标记
        evidence_field = None
        for ev_field in ['evidence', '证据', '取证单', 'source', '来源', '附件', '凭证']:
            if ev_field in f:
                evidence_field = ev_field
                break

        if evidence_field:
            ev_value = f[evidence_field]
            if isinstance(ev_value, str) and ev_value.strip():
                result.pass_check(f'发现「{title_short}」有证据标记',
                                   f'{evidence_field}: {ev_value[:60]}')
            elif isinstance(ev_value, list) and len(ev_value) > 0:
                result.pass_check(f'发现「{title_short}」有证据标记',
                                   f'{evidence_field}: {len(ev_value)} 项')
            else:
                result.fail(f'发现「{title_short}」证据非空',
                             f'{evidence_field} 字段为空')
        else:
            result.fail(f'发现「{title_short}」有证据字段',
                         '缺少 evidence/证据/取证单/来源 字段',
                         '请为每条发现添加 evidence 字段记录证据来源')

        # Check: 模糊词检查
        found_reds = [w for w in red_flags if w in f_text]
        if found_reds:
            result.fail(f'发现「{title_short}」无模糊表述',
                         f'含红词: {", ".join(found_reds)}',
                         '请将模糊表述改为确定性语言，如"经核查""经取证"')

        # Check: 法规引用
        reg_field = None
        for rf in ['regulation', '法规', '依据', 'law', '条款', '违规依据']:
            if rf in f:
                reg_field = rf
                break
        if reg_field:
            result.pass_check(f'发现「{title_short}」有法规引用',
                               f'{reg_field}: {str(f[reg_field])[:60]}')
        else:
            result.pass_check(f'发现「{title_short}」有法规引用',
                               '无独立法规字段（非致命，可能在描述中）')

        # Check: 金额验证
        amount_fields = ['amount', '金额', '涉及金额', '违规金额', '资金']
        for af in amount_fields:
            if af in f:
                try:
                    amt = float(f[af]) if f[af] else 0
                    if amt > 0:
                        result.pass_check(f'发现「{title_short}」金额为正数',
                                           f'{af}={amt:,.2f}')
                    elif amt == 0:
                        result.pass_check(f'发现「{title_short}」金额',
                                           f'{af}=0（零金额发现）')
                except:
                    pass
                break

    # 汇总验证
    total_amount = 0
    has_amount = 0
    for f in findings:
        for af in ['amount', '金额', '涉及金额', '违规金额']:
            if af in f:
                try:
                    total_amount += float(f[af])
                    has_amount += 1
                except:
                    pass
                break

    if has_amount > 1:
        result.pass_check(f'金额汇总检查',
                           f'{has_amount} 条发现含金额, 合计 ¥{total_amount:,.2f}')
        # 检查是否有汇总文件与合计一致
        summary_file = os.path.join(project_dir, 'findings', '_summary.json')
        if os.path.exists(summary_file):
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                summary_total = summary.get('total_amount', summary.get('合计', 0))
                if abs(summary_total - total_amount) < 0.01:
                    result.pass_check('汇总金额交叉验证',
                                       f'汇总表 ¥{summary_total:,.2f} = 各发现合计 ¥{total_amount:,.2f} ✅')
                else:
                    result.fail('汇总金额交叉验证',
                                 f'汇总表 ¥{summary_total:,.2f} ≠ 各发现合计 ¥{total_amount:,.2f}',
                                 '请核实汇总数与各发现金额是否一致')
            except:
                pass

    if not result.passed:
        result.suggested_action = result.suggested_action or (
            '请逐条核实以上拦截项:\n'
            '  1. 每条发现补充 evidence 字段\n'
            '  2. 替换模糊表述为确定性语言\n'
            '  3. 确认汇总金额与各发现合计一致')

    return result


# ============================================================
# CLI 入口
# ============================================================

GATE_REGISTRY = {
    'preaudit': gate_preaudit,
    'evidence': gate_evidence,
}

def main():
    parser = argparse.ArgumentParser(description='审盾 HARD-GATE 执行引擎')
    parser.add_argument('--project', '-p', required=True, help='项目名称或路径')
    parser.add_argument('--gate', '-g', choices=list(GATE_REGISTRY.keys()),
                        help='Gate 名称 (preaudit / evidence)')
    parser.add_argument('--findings', '-f', default='', help='发现文件路径 (仅 evidence gate)')
    parser.add_argument('--all', action='store_true', help='运行所有 Gate')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--list', action='store_true', help='列出可用 Gate')

    args = parser.parse_args()

    if args.list:
        print('可用 Gate:')
        for name in GATE_REGISTRY:
            desc = {
                'preaudit': '审前策划 — 方案未经确认，不得进场',
                'evidence': '证据闭环 — 没有证据，不得宣称已确认',
            }.get(name, '')
            print(f'  {name:15s} {desc}')
        return

    if args.gate:
        gates_to_run = [args.gate]
    elif args.all:
        gates_to_run = list(GATE_REGISTRY.keys())
    else:
        parser.print_help()
        return

    all_passed = True
    all_results = []

    for gate_name in gates_to_run:
        gate_fn = GATE_REGISTRY[gate_name]

        if gate_name == 'evidence' and not args.findings:
            result = gate_fn(args.project)
        elif gate_name == 'evidence':
            result = gate_fn(args.project, args.findings)
        else:
            result = gate_fn(args.project)

        all_results.append(result.to_dict())
        if not result.passed:
            all_passed = False

        if not args.json:
            print(f'\n  {"="*50}')
            result.print_report()
        else:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    # 汇总
    if not args.json and len(gates_to_run) > 1:
        passed_count = sum(1 for r in all_results if r['passed'])
        print(f'\n  {"="*50}')
        print(f'  审盾 Gate 汇总: {passed_count}/{len(gates_to_run)} 通过')
        if all_passed:
            print(f'  🎉 ALL GATES PASSED — 可以继续')
        else:
            print(f'  🚫 SOME GATES BLOCKED — 请修正后重试')

    # 退出码
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()

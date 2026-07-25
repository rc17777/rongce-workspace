# -*- coding: utf-8 -*-
"""
Error Hub 错误共享库 v1.0
=========================
灵感来源：AgentDebugX 的 Error Hub

功能：
  1. 存储脱敏后的"失败-诊断-修复"包
  2. 作为 CI 回归测试用例
  3. 跨项目、跨Agent的错误模式对比
  4. 可复用的调试记忆

用法：
  python agent_error_hub.py --project "XX项目" --action store
  python agent_error_hub.py --project "XX项目" --action store --error "handover_context_loss"
  python agent_error_hub.py --action query --pattern "early_termination"
  python agent_error_hub.py --action stats              # 错误统计
  python agent_error_hub.py --action test --project "XX项目"   # 回归测试
  python agent_error_hub.py --action compare --projects "项目A,项目B"  # 跨项目对比
"""

import os, sys, json, re, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')
CST = timezone(timedelta(hours=8))

WORKSPACE = Path(__file__).parent.parent
BLACKBOARD = WORKSPACE / 'audit-blackboard'
PROJECTS = BLACKBOARD / 'projects'
DEBUG_DIR = BLACKBOARD / 'debug'
ERROR_HUB_DIR = BLACKBOARD / 'error_hub'
ERROR_HUB_DIR.mkdir(parents=True, exist_ok=True)

ERROR_INDEX_PATH = ERROR_HUB_DIR / 'index.json'
REGRESSION_PATH = ERROR_HUB_DIR / 'regression_cases.json'


class ErrorHub:
    """
    Error Hub 错误共享库。
    对标 AgentDebugX 的 Error Hub + 共享错误库功能。
    """

    def __init__(self):
        self.index = self._load_index()
        self.regression_cases = self._load_regression()

    def _load_index(self):
        if ERROR_INDEX_PATH.exists():
            return json.loads(ERROR_INDEX_PATH.read_text(encoding='utf-8'))
        return {'errors': [], 'stats': {'total': 0, 'by_type': {}, 'by_agent': {}, 'by_project': {}}}

    def _save_index(self):
        ERROR_INDEX_PATH.write_text(json.dumps(self.index, ensure_ascii=False, indent=2), encoding='utf-8')

    def _load_regression(self):
        if REGRESSION_PATH.exists():
            return json.loads(REGRESSION_PATH.read_text(encoding='utf-8'))
        return {'cases': []}

    def _save_regression(self):
        REGRESSION_PATH.write_text(json.dumps(self.regression_cases, ensure_ascii=False, indent=2), encoding='utf-8')

    def store(self, project_slug, error_type=None):
        """
        扫描项目的调试报告，存入Error Hub。
        自动脱敏（移除具体金额、人名、企业名等）。
        """
        project_debug_dir = DEBUG_DIR
        stored = 0

        # 收集所有调试产物
        sources = []
        for pattern in [f'rules_{project_slug}_*.json', f'deepdebug_{project_slug}_*.json']:
            for f in sorted(project_debug_dir.glob(pattern)):
                sources.append(f)

        if not sources:
            print(f"⚠️  项目 {project_slug} 无调试产物，先运行 agent_debug_rules.py 或 agent_deep_debug.py")
            return []

        errors_stored = []
        for src in sources:
            try:
                data = json.loads(src.read_text(encoding='utf-8'))
            except:
                continue

            # 提取错误条目
            items = []
            if 'issues' in data:
                items = data['issues']
            elif 'diagnosis' in data and 'root_causes' in data['diagnosis']:
                items = data['diagnosis']['root_causes']

            for item in items:
                # 脱敏处理
                sanitized = self._sanitize(item)

                # 生成唯一指纹（用于去重）
                fingerprint = self._fingerprint(sanitized)

                # 检查是否已存在
                existing = [e for e in self.index['errors'] if e.get('fingerprint') == fingerprint]
                if existing:
                    # 更新出现次数
                    existing[0]['occurrences'] = existing[0].get('occurrences', 1) + 1
                    existing[0]['last_seen'] = datetime.now(CST).isoformat()
                    existing[0]['projects'].append(project_slug)
                    existing[0]['projects'] = list(set(existing[0]['projects']))
                    continue

                error_entry = {
                    'id': f"ERR-{len(self.index['errors']) + 1:04d}",
                    'fingerprint': fingerprint,
                    'type': error_type or sanitized.get('rule_id', sanitized.get('id', 'unknown')),
                    'severity': sanitized.get('severity', 'P2'),
                    'description': sanitized.get('desc', sanitized.get('description', str(sanitized)[:200])),
                    'agent': sanitized.get('agent', sanitized.get('source_agent', 'unknown')),
                    'project': project_slug,
                    'projects': [project_slug],
                    'root_cause': sanitized.get('cause', {}).get('desc', ''),
                    'fix_applied': sanitized.get('fix', ''),
                    'source_file': src.name,
                    'created_at': sanitized.get('timestamp', datetime.now(CST).isoformat()),
                    'last_seen': datetime.now(CST).isoformat(),
                    'occurrences': 1,
                    'status': 'open',
                    'tags': self._auto_tag(sanitized),
                }

                self.index['errors'].append(error_entry)
                errors_stored.append(error_entry)
                stored += 1

        # 更新统计
        self.index['stats']['total'] = len(self.index['errors'])
        self.index['stats']['by_type'] = dict(Counter(e['type'] for e in self.index['errors']))
        self.index['stats']['by_agent'] = dict(Counter(e['agent'] for e in self.index['errors']))
        self.index['stats']['by_project'] = dict(Counter(
            p for e in self.index['errors'] for p in e['projects']
        ))
        self.index['stats']['by_severity'] = dict(Counter(e['severity'] for e in self.index['errors']))

        self._save_index()

        # 同时生成/更新回归测试用例
        self._generate_regression(error_type)

        print(f"✅ 已存储 {stored} 条错误记录（{len(self.index['errors'])} 条总计）")
        return errors_stored

    def _sanitize(self, item):
        """脱敏处理：移除具体金额、企业名、人名等。"""
        if isinstance(item, str):
            return {'description': item}

        result = {}
        for k, v in item.items():
            if isinstance(v, str):
                # 金额脱敏
                v = re.sub(r'\d{4,}(?:\.\d+)?\s*(?:元|万元|亿)', '[金额]', v)
                # 日期保留格式但改具体值
                v = re.sub(r'\d{4}-\d{2}-\d{2}', '[日期]', v)
                # 企业名脱敏（保留"公司"标记）
                v = re.sub(r'[\u4e00-\u9fff]{2,}(?:有限公司|集团|公司|事务所)', '[企业]', v)
                # 人名脱敏
                v = re.sub(r'(?:张某|李某|王某|赵某|[张李王赵刘陈杨黄周吴][\u4e00-\u9fff])', '[人员]', v)
                # 手机号脱敏
                v = re.sub(r'1[3-9]\d{9}', '[手机号]', v)
                # 身份证号脱敏
                v = re.sub(r'\d{17}[\dXx]', '[身份证号]', v)
                result[k] = v
            elif isinstance(v, dict):
                result[k] = self._sanitize(v)
            elif isinstance(v, list):
                result[k] = [self._sanitize(i) if isinstance(i, dict) else i for i in v]
            else:
                result[k] = v
        return result

    def _fingerprint(self, item):
        """生成错误指纹（用于去重）。"""
        # 取关键字段做hash
        key = f"{item.get('rule_id', '')}|{item.get('desc', '')}|{item.get('severity', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def _auto_tag(self, item):
        """根据描述自动打标签。"""
        tags = []
        text = json.dumps(item, ensure_ascii=False)

        tag_map = {
            'format': ['格式', '字段', '缺少', '重复'],
            'logic': ['矛盾', '不一致', '不符', '冲突'],
            'handover': ['交接', 'handover', '上下文', '传递'],
            'regulation': ['法规', '条例', '规定', '政策'],
            'amount': ['金额', '元', '万元', '数量'],
            'data': ['数据', '格式', '解析', 'schema'],
            'model': ['幻觉', 'hallucination', '模型', '模型'],
            'tool': ['工具', '调用', 'tool', '参数'],
            'severity': ['严重程度', '分类', 'P0', 'P1'],
            'early_stop': ['过早', '终止', 'premature', '未完成'],
        }

        for tag, keywords in tag_map.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)

        return tags

    def query(self, pattern=None, tag=None, agent=None, project=None, severity=None, limit=20):
        """查询错误库。"""
        results = self.index['errors']

        if pattern:
            results = [e for e in results if pattern.lower() in json.dumps(e, ensure_ascii=False).lower()]
        if tag:
            results = [e for e in results if tag in e.get('tags', [])]
        if agent:
            results = [e for e in results if agent == e.get('agent')]
        if project:
            results = [e for e in results if project in e.get('projects', [])]
        if severity:
            results = [e for e in results if severity == e.get('severity')]

        results = results[:limit]

        if not results:
            print("未找到匹配的错误记录")
            return []

        print(f"\n找到 {len(results)} 条匹配（总计 {self.index['stats']['total']} 条）\n")
        for e in results:
            status_icon = '🔴' if e['severity'] == 'P0' else ('🟡' if e['severity'] == 'P1' else '🟢')
            tags_str = ', '.join(e.get('tags', []))
            print(f"  {status_icon} [{e['id']}] {e['type']}")
            print(f"     描述: {e['description'][:100]}")
            print(f"     Agent: {e['agent']} | 项目: {', '.join(e['projects'])}")
            print(f"     出现 {e['occurrences']} 次 | 标签: {tags_str}")
            if e.get('fix_applied'):
                print(f"     修复: {e['fix_applied'][:80]}")
            print()

        return results

    def stats(self):
        """错误库统计概览。"""
        s = self.index['stats']
        print(f"\n{'='*50}")
        print(f"📊 Error Hub 统计概览")
        print(f"{'='*50}")
        print(f"  总错误数: {s['total']}")
        print(f"\n  按严重程度:")
        for sev, count in sorted(s.get('by_severity', {}).items()):
            bar = '█' * min(count, 40)
            print(f"    {sev}: {count:3d} {bar}")
        print(f"\n  按错误类型 (Top 10):")
        for typ, count in sorted(s.get('by_type', {}).items(), key=lambda x: -x[1])[:10]:
            print(f"    {typ:30s}: {count:3d}")
        print(f"\n  按Agent (Top 10):")
        for agent, count in sorted(s.get('by_agent', {}).items(), key=lambda x: -x[1])[:10]:
            print(f"    {agent:20s}: {count:3d}")
        print(f"\n  按项目:")
        for proj, count in s.get('by_project', {}).items():
            print(f"    {proj:30s}: {count:3d}")

    def compare(self, project_slugs):
        """跨项目错误对比分析。"""
        projects = [p.strip() for p in project_slugs.split(',')]
        print(f"\n{'='*60}")
        print(f"📊 跨项目错误对比")
        print(f"{'='*60}\n")

        by_project = defaultdict(list)
        for e in self.index['errors']:
            for p in e['projects']:
                if p in projects:
                    by_project[p].append(e)

        # 共同的错误类型
        all_types = {}
        for proj in projects:
            types = set(e['type'] for e in by_project[proj])
            all_types[proj] = types
            print(f"  {proj}: {len(by_project[proj])} 条错误, {len(types)} 种类型")

        # 交集（共同错误）
        if len(projects) >= 2:
            common = set.intersection(*all_types.values())
            print(f"\n  共同错误类型 ({len(common)}):")
            for t in sorted(common):
                counts = {p: sum(1 for e in by_project[p] if e['type'] == t) for p in projects}
                print(f"    {t}: " + " | ".join(f"{p}={c}" for p, c in counts.items()))

        # 独有错误
        for proj in projects:
            others_union = set.union(*[all_types[p] for p in projects if p != proj]) if len(projects) > 1 else set()
            unique = all_types[proj] - others_union
            if unique:
                print(f"\n  {proj} 独有错误 ({len(unique)}):")
                for t in sorted(unique):
                    print(f"    - {t}")

    def _generate_regression(self, error_type=None):
        """
        从错误库生成回归测试用例。
        对标 AgentDebugX 的 Error Hub → CI 回归测试。
        """
        errors = self.index['errors']
        if error_type:
            errors = [e for e in errors if e['type'] == error_type]

        cases = []
        for e in errors[:50]:  # 最多50个用例
            case = {
                'id': f"REG-{len(cases) + 1:04d}",
                'error_id': e['id'],
                'type': e['type'],
                'description': e['description'],
                'expected_severity': e['severity'],
                'agent': e['agent'],
                'check': self._generate_check(e),
                'status': 'active',
                'created_at': datetime.now(CST).isoformat(),
            }
            cases.append(case)

        self.regression_cases['cases'].extend(cases)
        # 去重
        seen_ids = set()
        unique_cases = []
        for c in self.regression_cases['cases']:
            if c['error_id'] not in seen_ids:
                seen_ids.add(c['error_id'])
                unique_cases.append(c)
        self.regression_cases['cases'] = unique_cases

        self._save_regression()
        print(f"\n✅ 已生成 {len(cases)} 个回归测试用例（总计 {len(unique_cases)} 个）")

    def _generate_check(self, error_entry):
        """根据错误类型生成对应的检查逻辑。"""
        error_type = error_entry['type']
        checks = {
            'R001': '检查发现记录是否包含所有必填字段',
            'R002': '检查金额单位是否统一',
            'R005': '检查发现ID是否重复',
            'R101': '检查Agent输出是否存在自相矛盾',
            'R104': '检查Agent是否过早声明任务完成',
            'R201': '检查P0/P1级发现是否被正确分级',
            'R204': '检查审计发现是否包含取证来源',
            'R301': '检查交接包关键字段是否完整',
            'R305': '检查交接链是否连续无断裂',
            'RC001': '验证交接包goal/confirmed_facts字段',
            'RC004': '验证Agent输出满足任务完成条件',
            'RC007': '验证工具调用参数格式正确',
        }
        return checks.get(error_type.split('_')[0], f'通用检查: {error_entry["description"][:100]}')

    def run_regression(self, project_slug=None):
        """
        运行回归测试。如果有项目参数，则对比项目最近的规则检测报告。
        """
        cases = self.regression_cases.get('cases', [])
        if not cases:
            print("⚠️  没有回归测试用例，先 store 错误")
            return

        print(f"\n{'='*60}")
        print(f"🧪 回归测试 — {len(cases)} 个用例")
        print(f"{'='*60}\n")

        # 如果指定了项目，加载最新的规则检测报告
        known_issues = set()
        if project_slug:
            latest_rules = sorted(DEBUG_DIR.glob(f'rules_{project_slug}_*.json'), reverse=True)
            if latest_rules:
                try:
                    data = json.loads(latest_rules[0].read_text(encoding='utf-8'))
                    known_issues = set(
                        i.get('rule_id', '') for i in data.get('issues', [])
                    )
                except:
                    pass

        passed = 0
        failed = 0
        unknown = 0

        for case in cases:
            error_type = case.get('type', '')
            # 检查规则ID是否在已知问题中（回归检测：已知问题是否仍存在）
            if error_type in known_issues:
                print(f"  ❌ [{case['id']}] {case['type']}: {case['description'][:60]} — 问题仍存在")
                failed += 1
            elif error_type.startswith('RC') or error_type.startswith('R3'):
                # 根因和交接类：需要规则检测结果
                if project_slug:
                    print(f"  ⚠️  [{case['id']}] {case['type']}: 需最新规则检测确认")
                    unknown += 1
                else:
                    print(f"  ❓ [{case['id']}] {case['type']}: 需指定项目进行检测")
                    unknown += 1
            else:
                # 格式/逻辑类：通常可以通过规则检测发现
                if error_type in known_issues:
                    print(f"  ❌ [{case['id']}] {case['type']}: 回归失败")
                    failed += 1
                else:
                    print(f"  ✅ [{case['id']}] {case['type']}: 通过")
                    passed += 1

        print(f"\n{'─'*50}")
        print(f"  通过: {passed} | 失败: {failed} | 待确认: {unknown}")
        print(f"  {'⚠️ 存在已知未修复的回归问题' if failed > 0 else '✅ 回归测试全部通过' if passed == len(cases) else '❓ 部分用例需重新检测'}")

    def export(self, format='json'):
        """导出错误库。"""
        if format == 'json':
            path = ERROR_HUB_DIR / f'export_{datetime.now(CST).strftime("%Y%m%d")}.json'
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
            print(f"✅ 已导出: {path} ({len(self.index['errors'])} 条)")
        elif format == 'csv':
            import csv
            path = ERROR_HUB_DIR / f'export_{datetime.now(CST).strftime("%Y%m%d")}.csv'
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Type', 'Severity', 'Description', 'Agent', 'Projects', 'Occurrences', 'Tags'])
                for e in self.index['errors']:
                    writer.writerow([
                        e['id'], e['type'], e['severity'],
                        e['description'][:200], e['agent'],
                        ', '.join(e['projects']), e['occurrences'],
                        ', '.join(e.get('tags', []))
                    ])
            print(f"✅ 已导出: {path} ({len(self.index['errors'])} 条)")


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Error Hub 错误共享库')
    parser.add_argument('--project', default=None, help='项目标识')
    parser.add_argument('--action', choices=['store', 'query', 'stats', 'test', 'compare', 'export'], default='stats')
    parser.add_argument('--error', default=None, help='指定错误类型（store时）')
    parser.add_argument('--pattern', default=None, help='搜索关键词（query时）')
    parser.add_argument('--tag', default=None, help='按标签过滤（query时）')
    parser.add_argument('--agent', default=None, help='按Agent过滤')
    parser.add_argument('--severity', default=None, help='按严重程度过滤')
    parser.add_argument('--projects', default=None, help='跨项目对比（逗号分隔）')
    parser.add_argument('--format', default='json', help='导出格式（json/csv）')
    parser.add_argument('--limit', type=int, default=20, help='查询结果限制')
    args = parser.parse_args()

    hub = ErrorHub()

    if args.action == 'store':
        if not args.project:
            print("⚠️  store 需要 --project 参数")
        else:
            hub.store(args.project, args.error)
    elif args.action == 'query':
        hub.query(args.pattern, args.tag, args.agent, args.project, args.severity, args.limit)
    elif args.action == 'stats':
        hub.stats()
    elif args.action == 'test':
        hub.run_regression(args.project)
    elif args.action == 'compare':
        if not args.projects:
            print("⚠️  compare 需要 --projects 参数（逗号分隔）")
        else:
            hub.compare(args.projects)
    elif args.action == 'export':
        hub.export(args.format)
